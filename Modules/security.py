# 📁 Modules/security.py
import re
import html
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import sys
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)
from Config.pattern_injection import patterns

# --- 1. Nettoyage des sujets (subject)
def clean_subject(subject):
    subject = subject.strip()
    subject = html.unescape(subject)
    subject = re.sub(r'[\x00-\x1f\x7f]', '', subject)  # caractères non imprimables
    return subject


pattern = re.compile("|".join(patterns), re.IGNORECASE)

# --- 2. Nettoyage du body (XSS, prompt injection, scripts)
def clean_body_text(body):
    if not body:
        return ""
    
    body = html.unescape(body)
    
    # Supprime les tags HTML/JS potentiellement dangereux
    soup = BeautifulSoup(body, "html.parser")
    for tag in soup(["script", "style", "iframe", "meta", "object"]):
        tag.decompose()

    cleaned = soup.get_text()
    
    # Neutralisation des patterns d'injection LLM
    patterns = [
        r"(?i)^(ignore previous instructions)",
        r"(?i)(you are now)",
        r"(?i)(act as an expert)",
        r"(?i)(execute this code)",
        r"(?i)(<script.*?>.*?</script>)",
    ]
    for pattern in patterns:
        cleaned = re.sub(pattern, "[neutralized]", cleaned)

    return cleaned.strip()

# --- 3. Neutralisation des liens malveillants

def neutralize_links(body):
    url_pattern = r'(https?://[^\s\)]+)'
    return re.sub(url_pattern, r'[Lien supprimé]', body)

# --- 4. Validation stricte des champs

def validate_email_address(addr):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", addr))

def clean_date(date_str):
    if date_str and isinstance(date_str, str):
        return re.sub(r"[^0-9\-: ]", "", date_str.strip())
    return ""

# --- 5. Fonction principale à appeler : nettoyage complet d'un email

def sanitize_email_dict(email):
    email["subject"] = clean_body_text(clean_subject(email.get("subject", "")))
    #email["subject"]=email['subject']
    email_body_size_before = len(email['body_long'])
    email["body"] = clean_body_text(email.get("body", ""))
    email["body"] = neutralize_links(email["body"])
    email["body_long"] = clean_body_text(email.get("body_long", ""))
    email["body_long"] = neutralize_links(email["body_long"])
    email_body_size_after = len(email['body_long'])


    email["from"] = email.get("from", "").strip()
    email["to"] = email.get("to", "").strip()

    if not validate_email_address(email["from"]):
        pass
        #email["from"] = "invalid@unknown.com"
    if not validate_email_address(email["to"]):
        pass
        #email["to"] = "invalid@unknown.com"

    email["date"] = clean_date(email.get("date", ""))
    #print(email_body_size_before, email_body_size_after)

    return email
