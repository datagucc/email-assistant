import os
import re
import sys
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)
from Config.config import IMAP_SERVER, IMAP_PORT, IMAP_USER, IMAP_PASSWORD, data_folder_output, my_mail_digest
summaries_path = data_folder_output+'/'+'summaries'



def parse_date_from_filename(filename):
    # Exemple : "2025-07-05_2025-07-06_7634cc68a62b.txt"
    return datetime.strptime(filename.split('_')[0], "%Y-%m-%d")

def load_summary_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def extract_pertinence(summary_text):
    match = re.search(r'___([\d.]+)___', summary_text)
    if match:
        return float(match.group(1))
    return 0.0  # Valeur par défaut si non trouvée

def get_summaries_for_week(start_date, end_date):
    
    summaries = []
    for file in os.listdir(summaries_path):
        if not file.endswith('.txt'):
            continue
        date_mail = parse_date_from_filename(file)
        if start_date <= date_mail <= end_date:
            path = os.path.join(summaries_path, file)
            content = load_summary_file(path)
            pertinence = extract_pertinence(content)
            summaries.append({
                "filename": file,
                "date_mail": date_mail,
                "summary": content,
                "pertinence": pertinence
            })
    return sorted(summaries, key=lambda x: x['pertinence'], reverse=True)

def get_last_week_folder_name(date_to: str=None):
    """
    Retourne le nom du dossier correspondant à la semaine précédente
    (du lundi au dimanche), par rapport à la date du jour.

    Returns:
        str: Nom du dossier au format 'YYYY-MM-DD_to_YYYY-MM-DD'
    """
    if date_to ==None:
        today = datetime.today()
    else:
        today =  datetime.strptime(date_to, '%Y-%m-%d').date()

    

    # Aller au lundi de cette semaine
    this_monday = today - timedelta(days=today.weekday())

    # Calculer la semaine précédente
    last_monday = this_monday - timedelta(days=7)
    last_sunday = this_monday - timedelta(days=1)

    folder_name = f"{last_monday.strftime('%Y-%m-%d')}_to_{last_sunday.strftime('%Y-%m-%d')}"
    #print(folder_name)
    return folder_name

def get_summaries_per_folder(folder_name):
    summaries= []
    folder_path =summaries_path+'/'+folder_name
    if not os.path.exists(folder_path):
        return []
    for file in os.listdir(folder_path):
        if not file.endswith('.txt'):
            continue
        date_mail = parse_date_from_filename(file)
        path = os.path.join(folder_path,file)
        content = load_summary_file(path)
        pertinence = extract_pertinence(content)
        summaries.append({
                "filename": file,
                "date_mail": date_mail,
                "summary": content,
                "pertinence": pertinence
            })
    return sorted(summaries, key=lambda x: x['pertinence'], reverse=True)

def build_report(summaries, folder_name: str):
    lines = []
    folder_name = folder_name.replace('_',' ')
    lines.append(f"Résumé hebdomadaire des newsletters du {folder_name} - {len(summaries)} articles\n\n")
    for s in summaries:
        lines.append(f"Date mail: {s['date_mail'].strftime('%Y-%m-%d')}, Pertinence: {s['pertinence']:.2f}\n")
        lines.append(s['summary'])
        lines.append("\n" + "-"*50 + "\n")
    return "\n".join(lines)




def send_email(report, daterange, to_email= my_mail_digest):
    from_email = IMAP_USER
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    password = IMAP_PASSWORD

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    #msg['Subject'] = "Résumé hebdo des newsletters Data"
    msg['Subject'] = f"Résumé hebdo des newsletters Data ({daterange})"

    msg.attach(MIMEText(report, 'plain'))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(from_email, password)
    server.send_message(msg)
    server.quit()
    print(f"Weekly {daterange} digest summaries sent to : {to_email}. ")


def automatic_report(date_to: str=None):
    if date_to ==None:
        today = datetime.today()
    else:
        today =  datetime.strptime(date_to, '%Y-%m-%d').date()
    if today.weekday()==0 or date_to!= None:
        folder_name = get_last_week_folder_name(date_to)
        summaries = get_summaries_per_folder(folder_name)
        report = build_report(summaries,folder_name)
        start_week = today - timedelta(days=today.weekday() )
        end_week = start_week + timedelta(days=6)
        date_range_str =  f"{start_week.strftime('%d/%m/%Y')} - {end_week.strftime('%d/%m/%Y')}"
        send_email(report,date_range_str)


