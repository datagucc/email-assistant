# 📬 Assistant Email Intelligent (en local)

Assistant personnel en Python pour trier, résumer, prioriser et pré-rédiger des réponses aux emails, sans dépendre de solutions SaaS externes.

---

## ✅ Fonctionnalités actuelles (Phase 1)

- Structure de projet modulaire prête à évoluer
- Connexion sécurisée à une boîte email via IMAP
- Appels API OpenAI (GPT-3.5-turbo) testés et fonctionnels
- Interface en ligne de commande (CLI)
- Variables sensibles externalisées via `.env`

---

## 🚀 Installation

### 1. Clone du projet

```bash
git clone git@github.com:ton-utilisateur/email-assistant.git
cd email-assistant
```
### 2. Creation du env virtuel
python -m venv venv
source venv/bin/activate

### 3. Installation des dépendances
pip install -r requirements.txt

---
## Configuration
Creer un fichier .env à la racine (--> génération d'un mot de passe d'application pr gmail https://myaccount.google.com/apppasswords + generation d'une clé apI sur openai : https://platform.openai.com/ )
```
# Connexion IMAP
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USER=ton.email@gmail.com
IMAP_PASSWORD=mot_de_passe_application_gmail

# Clé API OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Autres options
LANGUAGE_PREFERENCE=auto
OUTPUT_DIR=outputs
``
