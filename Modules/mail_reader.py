# parser.py

#Parsing .eml : lecture locale de mails exportés
#Sert à traiter :
# Des mails sauvegardés ou archivés (tests offline, backups…)
# Des corpus d'entraînement (style, fine-tuning)
# Ne nécessite aucune connexion réseau
# Très utile pour le développement, le test ou le style transfer
# Elle est utilisée en mode offline ou test reproductible.

import os
import imaplib  # For accessing emails via IMAP protocol
import email  # For parsing email messages
from Config.config import IMAP_SERVER, IMAP_PORT, IMAP_USER, IMAP_PASSWORD  # Import IMAP configuration
import email
from email import policy
from email.header import decode_header
from datetime import datetime
import re
import sys
from email.utils import parsedate_to_datetime
from langdetect import detect
from googleapiclient.discovery import build
from email import message_from_bytes
from base64 import urlsafe_b64decode
import time


project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)
# Prototypes par catégorie
from Config.config import max_size_body, flag_phrases

#from Modules.gmail_service import get_gmail_service


# CLEANING AND EXTRACTING FUNCTIONS

def detect_language(text: str) -> str:
    """
    Détecte la langue principale du texte.
    Retourne 'fr', 'en', 'es'... ou 'unknown' si échec.
    """
    try:
        text = re.sub(r"http\S+", "", text)  # supprime les liens
        text = text.strip()
        if len(text.split()) < 5:
            return "unknown"  # trop court
        return detect(text)
    except:
        return "unknown"

def decode_mime_words(s):
    """
    Decodes MIME encoded words in email headers.
    MIME encoded words are a mechanism defined in RFC 2047 for encoding non-ASCII characters within email headers.

    Args:
        s (str): The string to decode.

    Returns:
        str: The decoded string.
    """
    if not s:
        return ""
    decoded = decode_header(s)
    return ''.join(
        str(t[0], t[1] or 'utf-8') if isinstance(t[0], bytes) else str(t[0])
        for t in decoded
    )

def extract_body(msg):
    """
    Extracts the body text from an email message.

    Args:
        msg (email.message.EmailMessage): The email message to process.

    Returns:
        str: The extracted body text.
    """
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_dispo = str(part.get("Content-Disposition"))

            if "attachment" in content_dispo:
                continue

            if content_type == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
                except:
                    continue
    else:
        try:
            return msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="replace")
        except:
            return ""
    return ""


def do_not_answer_flag(body: str=''):
    """
    Checks if the input string contains any of the specified flag phrases.

    Args:
        body (str): The input string to check.

    Returns:
        bool: True if any of the flag phrases are found in the string, False otherwise.
    """

    return any(phrase in body.lower() for phrase in flag_phrases)


def clean_text(text):
    if not text:
        return ""

    # Supprimer les liens hypertextes explicites (http, https, www...)
    text = re.sub(r"https?://\S+|www\.\S+", "[lien supprimé]", text)

    # Supprimer les emails inclus dans le texte (facultatif)
    text = re.sub(r"\S+@\S+", "[email supprimé]", text)

    # Réduire les espaces multiples à un seul
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def reduce_text(text, max_words = max_size_body):
    if not text:
        return ""
    # Réduire le texte si il est trop long.
    # Tronquer au nombre de mots max
    words = text.strip().split()
    if len(words) > max_words:
        text = " ".join(words[:max_words]) + "..."
    
    return text.strip()




# EXTRACT EMAIL FROM GMAIL
def gmail_date_to_epoch(date_str):
    """Convertit une date (YYYY-MM-DD) en timestamp (secondes)"""
    return int(time.mktime(datetime.strptime(date_str, "%Y-%m-%d").timetuple()))


def extract_email_date(message, headers):
    """
    Extrait la date d'un message Gmail de manière robuste.
    - headers : liste de dictionnaires (extrait de message["payload"]["headers"])
    - message : objet complet retourné par l'API Gmail

    Retourne une string formatée YYYY-MM-DD HH:MM:SS ou None.
    """

    
    def get_header(name):
        for h in headers:
            if h["name"].lower() == name.lower():
                return h["value"]
        return None

    # 1. Essayer de parser l'entête "Date"
    date_str = get_header("Date")
    date_obj = None

    if date_str:
        try:
            date_obj = parsedate_to_datetime(date_str)
        except Exception as e:
            print(f"⚠️ Erreur parsing date_str ({date_str}): {e}")
            date_obj = None

    # 2. Si échec, fallback sur internalDate
    if not date_obj:
        internal_date_ms = message.get("internalDate")
        if internal_date_ms:
            try:
                date_obj = datetime.fromtimestamp(int(internal_date_ms) / 1000)
            except Exception as e:
                print(f"⚠️ Erreur parsing internalDate: {e}")
                date_obj = None

    # 3. Format final
    if date_obj:
        return date_obj.strftime("%Y-%m-%d %H:%M:%S")
    return None



def fetch_emails_gmail_api(service, is_date=None, filter='after',user_id="me", limit=100, list_id: list=[], is_sent: bool=False):
    """
    Récupère les derniers emails via l'API Gmail.

    Args:
        service: objet service Gmail authentifié via build().
        user_id: utilisateur Gmail (par défaut "me").
        limit (int): nombre max de mails à récupérer.

    Returns:
        list: liste de dictionnaires email enrichis avec ID Gmail.
    """
    print("📡 Connexion à Gmail API...")
    messages =[]
    next_page_token=None

    #extraire les mails recus ou les mails envoyés
    if is_sent:
        labelID = ['SENT']
    else:
        labelID = ['INBOX']
    if len(list_id)>0:
        for i in list_id:
            response = service.users().messages().get(userId=user_id, id=i, format="full").execute()
            messages.append(response)
    else:
        while True:
            if is_date:
                #on pourrait mettre before:2025/09/03
                q = f"{filter}:{is_date}"
                
                response = service.users().messages().list(userId=user_id,q=q,labelIds=labelID, maxResults=limit, pageToken=next_page_token).execute()
            else:
                response = service.users().messages().list(userId=user_id, labelIds=labelID, maxResults=limit,pageToken=next_page_token).execute()
            
            # Liste les derniers messages
            messages.extend(response.get("messages", []))


            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        
        #messages = response.get("messages", [])

    emails = []

    for msg in messages:
        try:
            msg_id = msg["id"]
            full_msg = service.users().messages().get(userId=user_id, id=msg_id, format="full").execute()

            payload = full_msg.get("payload", {})
            headers = payload.get("headers", [])
            thread_id = full_msg.get("threadId")

            def get_header(name):
                return next((h["value"] for h in headers if h["name"].lower() == name.lower()), "")

            subject = decode_mime_words(get_header("Subject"))
            from_ = decode_mime_words(get_header("From"))
            to = decode_mime_words(get_header("To"))

            #Extraction de la date
            date = extract_email_date(msg,headers)


            # Extraction du body
            def extract_body(payload):
                if "parts" in payload:
                    for part in payload["parts"]:
                        if part.get("mimeType") == "text/plain":
                            body_data = part["body"].get("data")
                            if body_data:
                                return urlsafe_b64decode(body_data).decode("utf-8")
                elif payload.get("mimeType") == "text/plain":
                    body_data = payload["body"].get("data")
                    if body_data:
                        return urlsafe_b64decode(body_data).decode("utf-8")
                return ""

            body_long = clean_text(extract_body(payload))
            body = reduce_text(body_long)
            flag_no_answer = do_not_answer_flag(body)
            lang = detect_language(body)

            email_dict = {
                "email_id": msg_id,  # ID Gmail utile pour labeling ou lien
                "message_id": full_msg.get("id", ""),
                "thread_id":thread_id,
                "from": from_,
                "to": to,
                "subject": subject,
                "date": date,
                "body": body,
                "body_long": body_long,
                "lang": lang,
                "flag_no_answer": flag_no_answer
            }
            emails.append(email_dict)

        except Exception as e:
            print(f"❌ Erreur lecture mail ID {msg['id']}: {e}")

    print(f"✅ {len(emails)} emails récupérés via Gmail API.")
    return emails




# EXTRACTING EML MAILS
def parse_eml_file(filepath):
    try:
        with open(filepath, "rb") as f:
            msg = email.message_from_binary_file(f, policy=policy.default)

        message_id = msg.get("Message-ID", "").strip()
        from_ = decode_mime_words(msg.get("From", ""))
        to = decode_mime_words(msg.get("To", ""))
        subject = decode_mime_words(msg.get("Subject", ""))
        date_raw = msg.get("Date")
        date = email.utils.parsedate_to_datetime(date_raw).strftime("%Y-%m-%d %H:%M:%S") if date_raw else None
        body_long = clean_text(extract_body(msg))
        body = reduce_text(body_long)
        flag_no_answer = do_not_answer_flag(body)
        lang = detect_language(body)

        return {
            "email_id": message_id,
            "from": from_,
            "to": to,
            "subject": subject,
            "date": date,
            "body": body,
            "body_long":body_long,
            "lang": lang,
            "flag_no_answer":flag_no_answer

        }

    except Exception as e:
        print(f"⚠️ Erreur parsing {filepath} : {e}")
        return None

def parse_eml_directory(directory):
    mails = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(".eml"):
            path = os.path.join(directory, filename)
            mail = parse_eml_file(path)
            if mail:
                mails.append(mail)
    return mails



# EXTRACTING IMAP MAILS


def fetch_emails_imap(limit=20):
    """
    Fetches emails from an IMAP server.

    Args:
        limit (int): The maximum number of emails to fetch. Defaults to 20.

    Returns:
        list: A list of dictionaries, each representing an email.
    """
    print(f"🔌 Connecting to {IMAP_SERVER}...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)  # Connect to the IMAP server
    mail.login(IMAP_USER, IMAP_PASSWORD)  # Log in to the IMAP server
    mail.select("inbox")  # Select the inbox
    result, data = mail.search(None, "ALL")  # Search for all emails
    mail_ids = data[0].split()  # Get the list of email IDs
    last_ids = mail_ids[-limit:]  # Get the most recent email IDs
    emails = []  # List to store the fetched emails

    for i in reversed(last_ids):
        res, msg_data = mail.fetch(i, "(RFC822)")  # Fetch the email by ID
        if res != 'OK':
            continue
        raw_email = msg_data[0][1]  # Get the raw email data
        msg = email.message_from_bytes(raw_email)  # Parse the raw email data
        try:
            message_id = msg.get("Message-ID", "").strip()  # Get the message ID
            from_ = decode_mime_words(msg.get("From", ""))  # Get and decode the sender
            to = decode_mime_words(msg.get("To", ""))  # Get and decode the recipient
            subject = decode_mime_words(msg.get("Subject", ""))  # Get and decode the subject
            date_raw = msg.get("Date")  # Get the raw date
            # Parse and format the date
            date = email.utils.parsedate_to_datetime(date_raw).strftime("%Y-%m-%d %H:%M:%S") if date_raw else None
            body_long = clean_text(extract_body(msg))  # Extract and clean the body text
            body = reduce_text(body_long)
            flag_no_answer = do_not_answer_flag(body)
            lang = detect_language(body)
            email_dict = {
                "email_id": message_id,
                "from": from_,
                "to": to,
                "subject": subject,
                "date": date,
                "body": body,
                "body_long":body_long,
                "lang": lang,  # Placeholder for future language detection
                "flag_no_answer":flag_no_answer
            }
            emails.append(email_dict)  # Add the email dictionary to the list
        except Exception as e:
            print(f"⚠️ Error reading email: {e}")  # Print any errors that occur

    mail.logout()  # Log out from the IMAP server
    return emails  # Return the list of fetched emails







