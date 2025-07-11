import os
import re
import hashlib
import pandas as pd
import openpyxl
from datetime import datetime
import sys 
from pathlib import Path

project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)


from Config.config import token_path, credentials_path, my_mail, my_log_path, use_gmail,eml_folder, limit_mail, data_folder_output,logs_folder

ARCHIVE_DIR = logs_folder
log_file = my_log_path

#def generate_logfile_name(date:str):
 #   date_str = datetime.strptime(date,"%Y-%m-%d")
  #  month_str = date_str.strftime("%Y_%m")
   # log_file = f"{log_file}/{month_str}_email_log.xlsx"
    #return log_file


def sanitize_filename(text: str) -> str:
    """Nettoie les caractères pour nom de fichier."""
    return re.sub(r"[^\w\d_-]", "_", text.lower())[:50]


def file_exists(email_id: str, file_type: str, base_dir: str = data_folder_output, text_type : str='summary'):
    """
    Vérifie si un fichier summary ou draft existe déjà.
    
    Args:
        email_id (str): ID unique du mail
        file_type (str): "summary" ou "draft"
        base_dir (str): répertoire où sont stockés les fichiers

    Returns:
        bool: True si le fichier existe, False sinon
    """
    if text_type == 'summary':
        text_type='summaries'
    else:
        text_type='drafts'
    filename = f"{email_id}_{file_type}.txt"
    file_path = os.path.join(base_dir, file_type, filename)
    return os.path.exists(file_path)

def generate_email_id(email: dict) -> str:
    """Crée un ID unique basé sur hash du sujet, expéditeur, date."""
    raw = (email.get("subject", "") + email.get("from", "") + email.get("date", "")).encode("utf-8")
    hash_id = hashlib.sha256(raw).hexdigest()[:12]
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    return f"{date_prefix}_{hash_id}"


def init_log_file():
    """Crée un fichier Excel si inexistant.
    Un fichier excel doit exister par mois. (donc on en crée un nouveau chaque mois)."""
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
    if not os.path.exists(log_file):
        df = pd.DataFrame(columns=[
            "id", "date", "from", "subject", "category","classification_type","score","embedded_category","embedded_score_delta"
            ,"priority", "lang", "draft_file", "summary_file", "treated","flag_no_answer"
        ])
        df.to_excel(log_file, index=False)


def load_log():
    """Charge le log actuel."""
    init_log_file()
    return pd.read_excel(log_file)

def get_last_date(path =log_file):
    path = Path(path)
    if path.exists():
        try:
            df = pd.read_excel(path)
            df['date']= pd.to_datetime(df['date'])
            last_date = df['date'].max()
            last_date = last_date.strftime('%Y/%m/%d')
        except:
            last_date=None
    else:
        last_date=None

    return last_date


def already_logged(email_id: str, log_df: pd.DataFrame) -> bool:
    return email_id in log_df["id"].values

def verify_id(email_id):
    log_df = load_log()
    if already_logged(email_id, log_df):
        #print(f"⚠️ Mail déjà archivé (id={email_id}), ignoré.")
        return True
    else:
        return False

def archive_email_data(email: dict, classification: dict, has_draft, has_summary):
    """
    Archive les métadonnées du mail traité.
    """
    # 1. Générer ID unique
    #email_id = generate_email_id(email)
    email_id = email['email_id']
    log_df = load_log()
    if already_logged(email_id, log_df):
        print(f"⚠️ Mail déjà archivé (id={email_id}), ignoré.")
        return 'ignored'

    # 3. Construction de la ligne de log
    row = {
        #"id": email_id,
        "id": email['email_id'],
        "date": email.get("date", ""),
        "from": email.get("from", ""),
        "subject": email.get("subject", ""),
        "category": classification.get("category", ""),
        "classification_type": classification.get("classifi_type", ""),
        "score":classification.get("score",-1),
        "embedded_category":classification.get("embedded_category",""),
        "embedded_score_delta":classification.get("embedded_score_delta",""),
        "priority": "null",  # à compléter plus tard
        "lang": email.get("lang", ""),
        "draft_file": has_draft,
        "summary_file": has_summary,
        "treated": True,
        "flag_no_answer":email.get("flag_no_answer","")
    }

    # 4. Ajout au log
    log_df.loc[len(log_df)] = row
    log_df.to_excel(log_file, index=False)
    print(f"✅ Email archivé : {email_id}")
    return email_id

from datetime import datetime, timedelta
import os

def create_week_folder_from_date(input_date_str, folder_directory=None):
    """
    Crée un dossier au format 'YYYY-MM-DD_to_YYYY-MM-DD' correspondant à la semaine de la date donnée.

    Args:
        input_date_str (str): Une date au format 'YYYY-MM-DD' (ex: '2025-07-08')
    """
    # Convertir la chaîne en objet datetime
    input_date = datetime.strptime(input_date_str, "%Y-%m-%d")

    # Trouver le lundi de cette semaine (0 = lundi, 6 = dimanche)
    begin_of_week = input_date - timedelta(days=input_date.weekday())
    end_of_week = begin_of_week + timedelta(days=6)

    # Formater les dates
    folder_name = f"{begin_of_week.strftime('%Y-%m-%d')}_to_{end_of_week.strftime('%Y-%m-%d')}"
    if folder_directory ==None:
        folder_directory=data_folder_output
    folder_name = folder_directory+'/'+folder_name

    # Créer le dossier si pas encore présent
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"✅ Dossier créé : {folder_name}")
    else:
        pass
        #print(f" 📁Dossier déjà existant : {folder_name}")

    return folder_name


def save_text(email: dict, text: str, email_id : str, text_type: str, classification : str, directory: str = data_folder_output):
    """
    Sauvegarde un brouillon de réponse dans un fichier .txt structuré.
    """

    try: 
        
        if text_type =='draft':
            directory = directory+'/drafts'
        elif text_type == 'summary' :
            directory = directory+'/summaries'
        else:
            print('error in the type of text to store.')
            return "error"
 
        os.makedirs(directory, exist_ok=True)

        date = email.get("date", datetime.now().strftime("%Y-%m-%d"))[:10]
        folder_name = create_week_folder_from_date(date,directory)

        from_ = email.get("from", "unknown").split("<")[-1].replace(">", "").replace("@", "_at_")

        subject = sanitize_filename(email.get("subject", "no_subject"))

        label = classification if classification else "unknown"     

        filename = f"{date}_{email_id}.txt"
        filepath = os.path.join(folder_name, filename)


        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"📧 From : {from_}\n")
            f.write(f"🗓️  Received on : {date}\n")
            f.write(f"🏷️  Type : {label}\n")
            f.write(f"✉️  Subjet : {email.get('subject', '')}\n\n")
            f.write(f"📄 {text_type.capitalize()} generated :\n")
            f.write("-" * 40 + "\n")
            f.write(text + "\n")
            f.write("-" * 40 + "\n")

        print(f"✅ {text_type.capitalize()} saved as : {filepath}")
    except Exception as e:
        print("voici l'erreur dans save text: ", str(e))
        print(email)
        #raise ee