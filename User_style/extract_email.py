import json

import time
import csv
import os
from datetime import datetime, timedelta

import sys
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)

from Modules.mail_reader import   parse_eml_directory, fetch_emails_imap, fetch_emails_gmail_api
from Modules.gmail_service import get_gmail_service
from Config.config import token_path,credentials_path


service = get_gmail_service(token_path,credentials_path)
emails_sent = fetch_emails_gmail_api(service,list_id=['19509bc4404e2938'], is_sent=False)
#emails_sent = fetch_emails_gmail_api(service, is_sent=True)
i = 0
for mail in emails_sent:
    print("email numéro :", i+1)
    print(mail)
    i+=1

