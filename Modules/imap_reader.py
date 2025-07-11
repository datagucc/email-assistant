# imap_reader.py
# IMAP : connexion directe à ta boîte mail
# Sert à accéder à tes mails récents automatiquement (via Internet)
# Pratique pour la gestion en direct de tes emails quotidiens
# Nécessite un accès réseau sécurisé et identifiants
# Elle est utilisée en mode production ou test direct.


# Import necessary libraries
import imaplib  # For accessing emails via IMAP protocol
import email  # For parsing email messages
from Config.config import IMAP_SERVER, IMAP_PORT, IMAP_USER, IMAP_PASSWORD  # Import IMAP configuration
import os
import email
from email import policy
from email.header import decode_header
from datetime import datetime
import re
import sys
from langdetect import detect
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)
# Prototypes par catégorie
from Config.config import max_size_body


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
        return ''
     decoded = decode_header(s)
     return ''.join(
        str(t[0], t[1] or 'utf-8') if isinstance(t[0], bytes) else str(t[0])
        for t in decoded
     )


def clean_text(text, max_words = max_size_body):
    if not text:
        return ""

    # Supprimer les liens hypertextes explicites (http, https, www...)
    text = re.sub(r"https?://\S+|www\.\S+", "", text)

    # Supprimer les emails inclus dans le texte (facultatif)
    text = re.sub(r"\S+@\S+", "", text)

    # Réduire les espaces multiples à un seul
    text = re.sub(r"\s+", " ", text)

    # Réduire le texte si il est trop long.
    # Tronquer au nombre de mots max
    words = text.strip().split()
    if len(words) > max_words:
        text = " ".join(words[:max_words]) + "..."


    return text.strip()



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



def fetch_emails(limit=20):
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
            body = clean_text(extract_body(msg))  # Extract and clean the body text
            email_dict = {
                "message_id": message_id,
                "from": from_,
                "to": to,
                "subject": subject,
                "date": date,
                "body": body,
                "lang": None  # Placeholder for future language detection
            }
            emails.append(email_dict)  # Add the email dictionary to the list
        except Exception as e:
            print(f"⚠️ Error reading email: {e}")  # Print any errors that occur

    mail.logout()  # Log out from the IMAP server
    return emails  # Return the list of fetched emails
