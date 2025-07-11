import os
import sys 
import csv
import re
from datetime import datetime
from typing import Dict
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)

from Config.classification_label import LABELS, newsletters_email, admin_email, job_search_platforms_email, notifications_email, pro_email, perso_email, job_search_answers_email,job_search_applications_email, spam
from Config.config import similarity_threshold, delta_difference
from Modules.detect_label_semantic import   detect_label_semantic # ta fonction actuelle
from Modules.detect_label_llm import detect_label_llm  # fonction GPT que tu as validée


def extract_content(s):
    # Utiliser une expression régulière pour trouver le contenu entre chevrons
    match = re.search(r'<([^>]+)>', s)
    if match:
        return match.group(1)
    else:
        return s
    
def classify_with_fallback(email : Dict[str,str], similarity_threshold=similarity_threshold, delta_difference = delta_difference):
    """
    On tente d'abord de voir si le from fait parti d'une des adresses emails pré-enregistrées.
    Si on ne trouve rien, on tente la classification par embeddings.
    Si le score est trop bas, utilise le LLM en fallback.
    Retourne : (catégorie, méthode utilisée, score_embedding)
    """
    #Etape 0:
    category = 'none'
    email['frombis']=extract_content(email['from'])
    if email['frombis'] in newsletters_email:
        category = 'newsletters'  
    elif email['frombis'] in notifications_email:
        category = 'notifications'
    elif email['frombis'] in job_search_platforms_email:
        category = 'job_search_platforms'
    elif email['frombis'] in admin_email:
        category = 'administrative'
    elif email['frombis'] in job_search_applications_email:
        category = 'job_search_applications'
    elif email['frombis'] in job_search_answers_email:
        category = 'job_search_answers'
    elif email['frombis'] in pro_email:
        category = 'professional'
    elif email['frombis'] in perso_email:
        category = 'personal'
    if category != 'none':
        print(f"✅ Email {email['email_id']} classifié comme {category} via l'email list. ")
        return {'category':category, "classifi_type":"email_list", 'score':1,'delta': 0,'embedded_score_delta':"(0,0)",'llm_score':0,'embedded_category':'no_computed'}
    
    


    great_simi = 0.7
    # Étape 1 : tentative via embeddings
    semantic_dict = detect_label_semantic(email)
    category, score, delta = semantic_dict['label'],semantic_dict['score'], semantic_dict['delta']
    #print("semantic_dict: ",semantic_dict)

    if great_simi <= score or (similarity_threshold < score and delta > delta_difference ): 
        print(f"✅ Email {email['email_id']} classifié comme {category} via embedding, sur un score de {score} et un delta de {delta}. ")
        return {'category':category, "classifi_type":"embedding", 'score':score,'delta': delta, 'embedded_score_delta':f"({score},{delta})",'llm_score':0, 'embedded_category':category}
    else:
        # Étape 2 : fallback vers LLM
        dict_llm = detect_label_llm(email)
        category_llm= dict_llm['label']
        score_llm =dict_llm['score']
        delta_llm =-1
        print(f"✅ Email {email['email_id']} classifié comme {category_llm} via llm, sur un score de {score_llm}. La catégorie embedding était : {category} sur un score/delta : {score}/{delta}. ")
        return  {'category':category_llm, "classifi_type":"llm_fallback", 'score':score_llm,'delta': -1,'embedded_score_delta':f"({score},{delta})",'llm_score':score_llm,'embedded_category':category}
    





