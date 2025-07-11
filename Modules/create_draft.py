import re
import sys
import os
from datetime import datetime
from openai import OpenAI
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)



log_ai_path ='/Users/focus_profond/GIT_repo/utils'
if log_ai_path not in sys.path:
    sys.path.append(log_ai_path)
#charger le module de log chatgpt
from openAI_logger import log_openai_usage

# Prototypes par catégorie
from Config.prompting import PROMPTS_DRAFT_system, PROMPTS_DRAFT_user
from Config.config import model_draft, max_tokens_draft, style_user_path
from Config.user_style import user_style
from RAG.output.RAG_prompting import prompt_user, prompt_system, style_summary


# Charger la clé API OpenAI depuis une variable d'environnement
from Config.config import OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)




def generate_draft(email: dict, similar_examples: list=[], model : str=model_draft, max_tokens : int=max_tokens_draft, temperature: int=0.35) -> str:
    """
    Génère un brouillon de réponse à un email donné, dans la langue détectée.
    """
    
    subject = email.get("subject", "")
    #body = email.get("body", "")
    body = email.get("body_long", "")
    lang = email.get("lang", "fr")
    #content = f"Subjet : {subject}\n\nBody : {body}"

    if lang not in PROMPTS_DRAFT_system:
        lang = "fr"  # fallback



    #PROMPTING WITH EMBEDDED
    """prompt_user = prompt_user[lang].format(subject = subject
                                            ,body_long = body
                                            ,ex1_subject=similar_examples[0]["subject"],
                                            ex1_email_received=similar_examples[0]["email_received"],
                                            ex1_reply=similar_examples[0]["reply"],
                                            ex2_subject=similar_examples[1]["subject"],
                                            ex2_email_received=similar_examples[1]["email_received"],
                                            ex2_reply=similar_examples[1]["reply"],
                                            ex3_subject=similar_examples[2]["subject"],
                                            ex3_email_received=similar_examples[2]["email_received"],
                                            ex3_reply=similar_examples[2]["reply"])
    prompt_system = prompt_system[lang].format(user_style=user_style[lang])
    """

    #PROMPTING WITH JUST USER STYLE 
    prompt_system = PROMPTS_DRAFT_system[lang].format(user_style=user_style[lang])
    prompt_user =PROMPTS_DRAFT_user[lang].format(subject=subject,body=body)
    
    size_prompt = len(prompt_system+prompt_user)    

    try:
        response = client.chat.completions.create(
            model=model
            ,messages=[{"role": "system", "content": prompt_system}
                       ,{"role": "user", "content": prompt_user}]
            #au plus il va être faible, au plus l'IA sera feineante et pertinente.
            ,max_tokens=max_tokens
            ,temperature=temperature)
        
        #recuperation de la donnée
        draft = response.choices[0].message.content.strip()
        draft += f"\n Langue de l'email : {email['lang']}"
        

        log_openai_usage(response=response, response_text=draft,prompt=prompt_system, size_prompt=size_prompt, max_tokens=max_tokens,temperature=temperature, function_used="generate_draft", project="email_assistant")

        return {"draft":draft}

    except Exception as e:
        print(f"⚠️ Error during generation of draft : {e}")
        return {"draft":None} 


