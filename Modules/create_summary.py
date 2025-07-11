import re
import sys
from openai import OpenAI
from datetime import datetime
import os
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)

log_ai_path ='/Users/focus_profond/GIT_repo/utils'
if log_ai_path not in sys.path:
    sys.path.append(log_ai_path)
#charger le module de log chatgpt
from openAI_logger import log_openai_usage

# Prototypes par catégorie
from Config.prompting import  PROMPTS_SUMMARY_system, PROMPTS_SUMMARY_user
from Config.config import max_size_email, model_summary, max_tokens_summary


# Charger la clé API OpenAI depuis une variable d'environnement
from Config.config import OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)

def truncate_text(text, max_words=max_size_email):
    """Limite le texte à un nombre de mots max."""
    words = text.split()
    return " ".join(words[:max_words])


def get_gmail_link_0(email_id):
    return f"https://mail.google.com/mail/u/0/#all/{email_id}"

def get_gmail_link_1(email_id):
    return f"https://mail.google.com/mail/u/1/#all/{email_id}"

def get_gmail_link_2(email_id):
    return f"https://mail.google.com/mail/u/2/#all/{email_id}"

def generate_summary(email: dict, model : str=model_summary, max_tokens : int=max_tokens_summary, temperature: int=0.0) -> str:
    """
    Résume un email (subject + body) en 2–3 phrases, dans la langue détectée.
    Utilise GPT-3.5-Turbo via OpenAI API.
    """

    # 1. Préparation du contenu
    subject = email.get("subject", "")
    #body = email.get("body", "")
    body = email.get("body_long", "")
    content = truncate_text((subject + " " + body).strip(), max_words=max_size_email)

    # 2. Détection langue (par défaut français)
    lang = email.get("lang", "fr")
    if lang not in ["fr", "en", "es"]:
        lang = "fr"
        print(f"Langue not french, not english, not spanish but {lang}")

    # 3. Création du prompt
    
    prompt_system = PROMPTS_SUMMARY_system[lang]
    prompt_user =PROMPTS_SUMMARY_user[lang].format(email_content=content)
    size_prompt = len(prompt_system+prompt_user)  

    try:
        # 4. Appel OpenAI
        response = client.chat.completions.create(
            model=model
            ,messages=[{"role": "system", "content": prompt_system}
                       ,{"role": "user", "content": prompt_user}]
            #au plus il va être faible, au plus l'IA sera feineante et pertinente.
            ,max_tokens=max_tokens_summary
            ,temperature=temperature)
        
        # Récupération de la réponse
        summary = response.choices[0].message.content.strip()
        
        summary += f"\n Lire l'email : {get_gmail_link_0(email['email_id'])}"
        summary += f"\n Lire l'email : {get_gmail_link_1(email['email_id'])}"
        summary += f"\n Lire l'email : {get_gmail_link_2(email['email_id'])}"
        summary += f"\n Langue de l'email : {email['lang']}"
        #print(f"Summary: {response}; {summary}; {max_tokens};{temperature}.")
        log_openai_usage(response=response,prompt=prompt_system,size_prompt=size_prompt, response_text=summary,max_tokens=max_tokens,temperature=temperature, function_used="generate_summary", project="email_assistant")
        return {'summary':summary}

    except Exception as e:
        print(f"⚠️ Error during the creation of the summary: {e}")
        return  {"summary":None}




