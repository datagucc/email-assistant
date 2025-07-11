import time
import csv
import os
from datetime import datetime, timedelta

import sys
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)

#import personal modules and variables
from Config.config import token_path, credentials_path, use_gmail,eml_folder, limit_mail

from Modules.mail_reader import   parse_eml_directory, fetch_emails_imap, fetch_emails_gmail_api
from Modules.security import sanitize_email_dict
from Modules.detect_label import classify_with_fallback
from  Modules.create_summary import generate_summary
from Modules.create_draft  import generate_draft
from Modules.pipeline_functions import archive_email_data, verify_id, save_text, get_last_date
from Modules.digest_newsletters import automatic_report
from Modules.gmail_service import get_gmail_service, get_actual_email_address,mark_as_read, mark_as_unread,classify_and_label_email, create_gmail_draft  # Je dois checker les exceptions + mettre les specs + les bons types pr les arguments + traduire en anglais
                                                                                            # + définir pour chaque fonction si c'est une erreur bloquante ou non.
#from RAG.search_top_replies import get_similar_replies


# if we want to run it on the gmail account
if use_gmail:
     #we get the date of the last email analysed and stored (from pipeline function modules) 2025/09/12
     #lastdate= get_last_date()
     lastdate="2023/07/03"

     #we connect to the gmail service/app
     service = get_gmail_service(token_path,credentials_path)
     my_email_address = get_actual_email_address(service)

     
     #we extract all the emails that are the same date or after the lastdate
     emails=fetch_emails_gmail_api(service,lastdate,limit=limit_mail)
     
     #we extract all the emails that are the same date or before the date
     #emails=fetch_emails_gmail_api(service,'2024/01/01',limit=limit_mail)

     #we extract all the emails contained in the list_id 
     #emails=fetch_emails_gmail_api(service,lastdate,limit=limit_mail, list_id=['197c60c903a12d62'])


# if we want to run it on an batch of email stored in my local machine
else:
     emails = parse_eml_directory(eml_folder)

#we clean the data
emails = [sanitize_email_dict(email) for email in emails]
print("✅ The emails have been sanitized.")
# we initialise variables, than we start iterating
i=0
total_duration = 0
for mail in emails:
     
        print(f"\n--- MAIL {i+1} --- Subject : {mail['subject']} --- Date : {mail['date']}  --- ID : {mail['email_id']}")
        start_time = time.time()
        duration = 0

        #A. We check if the email exists in the log, if so, I continue with the next mail
        email_id = mail['email_id']
        is_new = verify_id(email_id)
        #is_new=False
        if is_new :
             print("We already analysed this email.")
             i+=1
             continue
        
        
        #B. Je classifie l'email en 3 étapes (s'il le faut)
        classification= classify_with_fallback(mail)
        category = classification.get("category")
        score = classification.get("score")
        method = classification.get("classifi_type")

        #C. J'applique le label sur gmail
        #print(f"category is : {category}. Method is: {method}. Score is : {score}")
        if use_gmail:
            classify_and_label_email(service,email_id, category)
            if category in ['newsletters','spam','notifications']:
                  classify_and_label_email(service,email_id,'to_delete')
                  if category=='notifications':
                    mark_as_unread(service,email_id)
                  else:
                    mark_as_read(service,email_id)
            if category in ['personal','professional']:
                 classify_and_label_email(service,email_id,'urgent')
                 mark_as_unread(service,email_id)
            
            


        has_summary = False
        has_draft = False
        if category == 'newsletters':
                #D. Je génère un résumé
                summary = generate_summary(mail)
                #E. Je sauve le résumé dans un fichier texte
                save_text(mail,summary['summary'],email_id,'summary', category )
                has_summary = True
        if category in ['professional','personal','administrative']:
                #F. Je génère un brouillon.
                #embedded_simi = get_similar_replies(mail['body_long'],mail['lang'])
                draft =generate_draft(mail)
                #draft =generate_draft(mail,embedded_simi)

                #G. J'enregistre le brouillon sur gmail
                draft_id = create_gmail_draft(service,mail, draft['draft'])
                #H. Je sauve le brouillon dans un fichier texte
                save_text(mail,draft['draft'],email_id,'draft', category )
                has_draft = True
        #I. Je sauve les logs de mon mail
        storage =archive_email_data(mail,classification, has_draft, has_summary)
        
        duration = round(time.time() - start_time, 2)
        total_duration +=duration
        i+=1

#automatic_report('2025-07-08')
automatic_report()

print(f"✅ Total duration {total_duration} en secondes, pour {i} mails.")


# 1er test full : before:  1.019.980 token = 0.68 --------- after : 1.115.347 tokens = 0.76 ; 4.01 pour 109 mails.


#2eme test full sur a.nollevaux.data@gmail.com : before : 1.124.774 tokens = 0.76 -------- after 


#3eme test full sur a.nollevaux.data@gmail.com : before : 1328000 , 0.89 ----> after: 

#"error on : 197c60c903a12d62"