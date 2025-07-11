import os
import pickle
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import re
from email.message import EmailMessage
from email.mime.text import MIMEText

import sys
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)

from Config.config import token_path, credentials_path


SCOPES = ['https://www.googleapis.com/auth/gmail.modify']  #permission of the authorization

# Authentifie l'utilisateur Gmail
def get_gmail_service(token_path=token_path, credentials_path=credentials_path):
    try:
        creds = Credentials.from_authorized_user_file(token_path)
        service = build('gmail', 'v1', credentials=creds)
    except Exception as e:
        print(f'Error connecting to the gmail service because of : {e}')
        raise e
    return service

# Vérifie et crée un label s’il n’existe pas
# on doit indiquer user_id = 'me' ! C'est une valeur spéciale qui signifie : le compte authentifié avec le token OAuth fourni.



def return_label_id(service,label_name, user_id='me'):
    try:
        labels = service.users().labels().list(userId=user_id).execute().get("labels", [])
        if label_name =='spam':
            label_name='spam_'
        for label in labels:
            if label["name"] == label_name:
                return label["id"]
        # Label non trouvé, on le crée
        label = {
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        }
        result = service.users().labels().create(userId=user_id, body=label).execute()
        return result["id"]
    except Exception as e:
        print(f'Error getting the label_id. Label name is :{label_name}')
        print(f'Error getting the label_id because of : {e}')
        raise e

# Applique le label au message : BON EXEMPLE D'UN BON TRY EXCEPT A INCLURE SUR TOUTES MES FONCTIONS
def label_email(service,  email_id, label_id,user_id='me'):
    """
    les 4 arguments sont importants :
    - la connexion à gmail (service)
    - le messageid
    - le label id
    - le user id (optionnel)
    """
    try:
        service.users().messages().modify(
            userId=user_id,
            id=email_id,
            body={"addLabelIds": [label_id]}
        ).execute()
    except Exception as e:
        print(f'Error labeling the email on Gmail because of : {e}')
        print(f'Here are the type of each arguments and the None values: {type(email_id)}, {type(label_id)}')
        raise e


def classify_and_label_email(service, email_id, category, user_id='me'):
    """
    Vérifie ou crée un label, puis l'applique à un message Gmail.

    Args:
        service: objet Gmail API connecté
        message_id: ID du message à labelliser
        category: nom du label à appliquer (ex: "personal", "newsletters", etc.)
        user_id: identifiant utilisateur Gmail (par défaut: "me")
    """

    try:
        # 1. Vérifie (ou crée) le label et récupère son ID
        label_id = return_label_id(service,  category,user_id)

        # 2. Applique le label
        label_email(service, email_id, label_id, user_id)
        #print("label_id : ",label_id)
        print(f"✅ Label '{category}' appliqué au message {email_id}.")

    except Exception as e:
        print(f"❌ Erreur application label '{category}' au message {email_id} : {e}")
        raise e


def mark_as_unread(service, email_id,user_id='me'):
    """
    Marque un message comme non lu (ajoute le label UNREAD)
    """
    try:
        service.users().messages().modify(
            userId=user_id,
            id=email_id,
            body={"addLabelIds": ["UNREAD"], "removeLabelIds": []}
        ).execute()
        print(f"📩 Email {email_id} marqué comme non lu.")
    except Exception as e:
        print(f"❌ Erreur marquage non-lu : {e}")
        #raise e

def mark_as_read(service, email_id,user_id='me'):
    """
    Marque un message comme  lu (supprime le label UNREAD)
    """
    try:
        service.users().messages().modify(
            userId=user_id,
            id=email_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
        print(f"📩 Email {email_id} marqué comme  lu.")
    except Exception as e:
        print(f"❌ Erreur marquage lu : {e}")
        #raise e


def create_gmail_draft(service, mail, draft, user_id='me'):
    """
    Enregistre un brouillon dans Gmail avec les informations fournies.
    
    Args:
        service: connexion authentifiée à l'API Gmail
        to (str): destinataire de l'email
        subject (str): sujet de l'email
        body (str): contenu texte du brouillon
        user_id (str): ID utilisateur Gmail (souvent 'me')
    
    Returns:
        draft_id (str): ID du brouillon créé
    """
    
    to =mail['from']
    subject = mail['subject']
    thread_id =mail['thread_id']
    from_ =mail['from']
    original_id = mail['email_id']

    # Debug print to check the email address
    #print(f"Debug - To: {to}, Subject: {subject}, Thread ID: {thread_id}, From: {from_}, Original ID: {original_id}")
    try:
        # Extract the email address using regular expressions, when the TO is an issue
        to_corrected = re.search(r'<([^>]+)>', to)
        if to_corrected:
            to = to_corrected.group(1)
        else:
            to = 'a.nollevaux.data@gmail.com'

        # Création du message au format MIME
        mime_message = MIMEText(draft)
        mime_message['To'] = to
        mime_message['From'] = from_
        mime_message['Subject'] = f"Re : {subject}"
        mime_message['In-Reply-To']= original_id
        mime_message['References']=original_id 


       # Encoder le message au format base64url
        encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()


        # Construction du corps de requête
        draft_body = {
            "message": {
                "raw": encoded_message
                ,"threadId":thread_id
            }
        }
        # Debug print to check the draft body
        print("Debug - Draft Body:", mime_message['To'], to)
        # Enregistrement du draft
        draft = service.users().drafts().create(userId=user_id, body=draft_body).execute()
        print(f"✅ Brouillon enregistré. Draft ID: {draft['id']}")
        mark_as_unread(service,original_id)
        return draft["id"]

    except Exception as e:
        print(f"❌ Erreur création brouillon : {e}")
        raise e


def get_actual_email_address(service):
    profile = service.users().getProfile(userId="me").execute()
    email_address = profile["emailAddress"]
    print(f"Connecté en tant que : {email_address}")
    return email_address