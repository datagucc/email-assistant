# parser.py

#Parsing .eml : lecture locale de mails exportés
#Sert à traiter :
# Des mails sauvegardés ou archivés (tests offline, backups…)
# Des corpus d'entraînement (style, fine-tuning)
# Ne nécessite aucune connexion réseau
# Très utile pour le développement, le test ou le style transfer
# Elle est utilisée en mode offline ou test reproductible.

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
    if not s:
        return ""
    decoded = decode_header(s)
    return ''.join(
        str(t[0], t[1] or 'utf-8') if isinstance(t[0], bytes) else str(t[0])
        for t in decoded
    )

def extract_body(msg):
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
        body = clean_text(extract_body(msg))
        body_long = extract_body(msg)
        lang = detect_language(body)

        return {
            "message_id": message_id,
            "from": from_,
            "to": to,
            "subject": subject,
            "date": date,
            "body": body,
            "body_long":body_long,
            "lang": lang
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
