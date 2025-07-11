# cette derniere méthode utilise un LLM pour classifier nos mails.
from openai import OpenAI
import os
import sys 
from typing import Dict
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)
log_ai_path ='/Users/focus_profond/GIT_repo/utils'
if log_ai_path not in sys.path:
    sys.path.append(log_ai_path)
#importer la lecture de mail

from Config.config import max_tokens_detection, model_detection

#charger le module de log chatgpt
from openAI_logger import log_openai_usage

# Charger la clé API OpenAI depuis une variable d'environnement
from Config.config import OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)
#openai.api_key = os.getenv("OPENAI_API_KEY")

# Liste des types autorisés
from Config.classification_label import LABELS
from Config.prompting import PROMPTS_CLASSIFICATION_SYSTEM,PROMPTS_CLASSIFICATION_USER
#CATEGORIES = ["pro", "perso", "admin", "newsletter", "notif", "spam"]

def detect_label_llm(email:  Dict[str, str], max_tokens : int =max_tokens_detection, temperature : float =0.0, model : str = model_detection) -> str:
    """
    Utilise GPT pour classer un email selon son type.
    Retourne une chaîne : ex. 'pro' ou 'spam'.
    """

    # Prompt simple et efficace

    prompt_system = PROMPTS_CLASSIFICATION_SYSTEM['fr']
    # 3. Création du prompt
    #prompt_system = PROMPTS_CLASSIFICATION_SYSTEM['fr'].format(content=LABELS)
    content_labels = ",".join(LABELS)
    content_body = email['body']
    if email['lang'] not in ['fr','es','en']:
        email['lang']='en'
    prompt_system = PROMPTS_CLASSIFICATION_SYSTEM[email['lang']].format(category_content=content_labels)
    prompt_user = PROMPTS_CLASSIFICATION_USER[email['lang']].format(email_content=content_body)

    size_prompt = len(prompt_system+prompt_user)  


  
    response = client.chat.completions.create(
            model=model
            ,messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user}]
            #au plus il va être faible, au plus l'IA sera feineante et pertinente.
            ,max_tokens=max_tokens
            ,temperature=temperature)
        
    # Récupération de la réponse
    summary = response.choices[0].message.content.strip().lower()
    try:
        label,score = summary.split(sep=";")
    except:
        label='no_category'
        score=-1
        
    usage = response.usage
    print(size_prompt)
    log_openai_usage(response, prompt_system,size_prompt,summary,max_tokens,temperature, function_used="detect_label_llm", project="email_assistant")

    #verification
    if summary in LABELS:
       # print(f"📊 Tokens utilisés : prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")
        return {'summary':summary, 'label':label, 'score':score}
    else:
        #print(f"📊 Tokens utilisés : prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")
        return {'summary':summary,'label':label, 'score':score}
    


