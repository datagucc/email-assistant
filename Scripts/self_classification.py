# generate_prototypes.py
from openai import OpenAI
import os
import json
import openai
from email import policy
from email.parser import BytesParser
# c'est utilisé pour créer une barre de progression pour les boucles et autres itérations.
from tqdm import tqdm
import sys
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)

from Modules.mail_reader import parse_eml_file

# Configure ton API key
from Config.config import OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)



# Répertoire contenant les sous-dossiers par catégorie
#BASE_DIR = "categorized_emails"
BASE_DIR ="/Users/focus_profond/GIT_repo/email_assistant/Data/input/eml_categories"
OUTPUT_DIR = "/Users/focus_profond/GIT_repo/email_assistant/Data/prototypes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Liste des nouvelles catégories
CATEGORIES = [
    "professional", "personal", "administrative", "newsletters",
    "notifications", "job_search_answers", "job_search_applications",
    "job_search_platforms", "spam"
]

def extract_body_from_eml(filepath):
    """Extrait le body texte d’un .eml"""
    with open(filepath, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    subject = msg.get("Subject", "")
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body += part.get_content().strip() + "\n"
                except:
                    continue
    else:
        try:
            body = msg.get_content()
        except:
            pass
    return (subject + "\n" + body).strip()



def summarize_with_gpt(text, category,lang='fr'):
    """Appelle l’API GPT pour créer un prototype synthétique"""
    if lang=='fr':
        lang='francais'
    elif lang =='es':
        lang='espagnol'
    else:
        lang='anglais'
    prompt = f"""
Lis cet email ci-dessous et transforme-le en un prototype clair, fluide et typique d’un email de type «{category}».

Règles :
- Résume le contenu sans inventer ni paraphraser inutilement.
- Ne change pas de ton.
- Le texte final (= le prototype) doit être en {lang}
- Le texte final (=le prototype) doit faire entre 3 et 8 lignes, être fluide et représentatif.
- Ne précise pas que c’est un résumé.
- Ne mentionne pas que tu es un assistant IA.

Email original :
{text}

Prototype :
"""
    try:
        #return response.choices[0].message.content.strip()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo"
            ,messages=[
                {"role":"system", "content":"Tu es un assistant spécialisé en catégorisation d'emails. Ton but est de produire un exemple représentatif (prototype) d'un mail pour une catégorie donnée."}
                ,{"role": "user", "content": prompt.strip()}]
            #au plus il va être faible, au plus l'IA sera feineante et pertinente.
            ,max_tokens=200
            ,temperature=0.3)
        
        # Récupération de la réponse
        prototype = response.choices[0].message.content.strip().lower()
        return prototype

    except Exception as e:
        print(f"⚠️ Erreur GPT : {e}")
        return None


def process_category(category):
    """Génère les prototypes d’une catégorie"""
    folder_path = os.path.join(BASE_DIR, category)
    prototypes = []
    files = [f for f in os.listdir(folder_path) if f.endswith(".eml")]

    print(f"\n📂 Traitement catégorie: {category} ({len(files)} mails)")
    for filename in tqdm(files):
        path = os.path.join(folder_path, filename)
        #je vais plutot appeler eml_reader qui permet de limiter et nettoyer le body.
        dict_email= parse_eml_file(path)
        body = dict_email['body']
        subject = dict_email['subject']
        lang = dict_email['lang']
        raw_text=(subject + "\n" + body).strip() 
        #raw_text = extract_body_from_eml(path)

        if len(raw_text.split()) < 30:  # Évite les mails trop courts
            continue

        prototype = summarize_with_gpt(raw_text, category,lang)
        if prototype:
            prototypes.append(prototype)

    # Sauvegarde
    outpath = os.path.join(OUTPUT_DIR, f"{category}_prototypes.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(prototypes, f, ensure_ascii=False, indent=2)
    print(f"✅ Sauvegardé : {outpath} ({len(prototypes)} prototypes)")


def main():
    for category in CATEGORIES:
        #if category not in ['spam','administrative','personal','professional']:
        if category =='newsletters':
            process_category(category)


if __name__ == "__main__":
    main()


#usage avant classification : 74 759
#usage après classification : 220 934 (mais j'ai du le recommencer plusieurs fois, j'i pas été super précis)
# dans tout les cas, ça a couté litterallement moins de 10 centimes.

#usage après l'avoir exécuté sur 11 éléments : 228 139