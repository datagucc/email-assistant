from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle

# Scopes nécessaires pour lire et modifier les emails
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
credentials_path ='/Users/focus_profond/GIT_repo/email_assistant/Config/credentials.json'
token_path = '/Users/focus_profond/GIT_repo/email_assistant/Config/token_augustinsubscribe.json'
token_path = '/Users/focus_profond/GIT_repo/email_assistant/Config/token_augustindata.json'


#pour générer le token, il ne faut pas fournir d'adresse email. C'est l'utilisateur lui-même qui le fournit et qui l'active au moment de l'ouverture du lien.
def get_token(credentials_path=credentials_path, token_path=token_path):
    creds = None
    if os.path.exists(token_path):
        print("✅ Token déjà existant")
        return token_path  # rien à faire

    # Authentification via navigateur
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)

    # Sauvegarde du token
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    print(f"✅ Token sauvegardé dans {token_path}")
    return token_path

# Exécuter une seule fois pour chaque utilisateur
get_token()
