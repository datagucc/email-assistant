import sys
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


from Modules.gmail_service import get_gmail_service,mark_as_read, mark_as_unread,classify_and_label_email, create_gmail_draft  # Je dois checker les exceptions + mettre les specs + les bons types pr les arguments + traduire en anglais
from Config.config import token_path, credentials_path, my_mail, my_log_path, data_folder, use_gmail,eml_folder, limit_mail

LABEL_COLOR_MAPPING_old = {
    "urgent":             {"backgroundColor": "#d93025", "textColor": "#ffffff"},  # rouge
    "professional":       {"backgroundColor": "#188038", "textColor": "#ffffff"},  # vert foncé
    "personal":           {"backgroundColor": "#34a853", "textColor": "#ffffff"},  # vert clair
    "notifications":      {"backgroundColor": "#4285f4", "textColor": "#ffffff"},  # bleu
    "no_category":        {"backgroundColor": "#ea4335", "textColor": "#ffffff"},  # rouge clair
    "job_search_answers": {"backgroundColor": "#fbbc04", "textColor": "#000000"},  # orange
    "job_search_applications": {"backgroundColor": "#9aa0a6", "textColor": "#000000"},  # gris
    "job_search_platforms":    {"backgroundColor": "#70757a", "textColor": "#ffffff"},  # gris foncé
    "newsletters":        {"backgroundColor": "#e8eaed", "textColor": "#000000"},  # gris très clair
    "administrative":     {"backgroundColor": "#1967d2", "textColor": "#ffffff"},  # bleu foncé
    "spam":               {"backgroundColor": "#5f6368", "textColor": "#ffffff"},  # gris/noir
    "to_delete":          {"backgroundColor": "#000000", "textColor": "#ffffff"},  # noir

}
LABEL_COLOR_MAPPING = {
    # 🔴 Catégories prioritaires – visibles et contrastées
    "urgent":             {"backgroundColor": "#cc3a21", "textColor": "#ffffff"},  # rouge vif
    "professional":       {"backgroundColor": "#0b804b", "textColor": "#ffffff"},  # vert foncé
    "personal":           {"backgroundColor": "#16a766", "textColor": "#ffffff"},  # vert franc
    "administrative":     {"backgroundColor": "#285bac", "textColor": "#ffffff"},  # bleu foncé

    # 🟠 Notifications importantes – ressortent modérément
    "job_search_answers": {"backgroundColor": "#f2c960", "textColor": "#ffffff"},  # jaune soutenu
    "notifications":      {"backgroundColor": "#4986e7", "textColor": "#000000"},  # bleu clair

    # ⚪️ Inconnus ou à supprimer – bien visibles mais différenciés
    "no_category":        {"backgroundColor": "#e66550", "textColor": "#ffffff"},  # rouge doux
    "unknown":        {"backgroundColor": "#e66550", "textColor": "#ffffff"},  # rouge doux
    "to_delete":          {"backgroundColor": "#efefef", "textColor": "#999999"},  # très discret, gris clair sur gris

    # 🔘 Catégories secondaires – plus discrètes
    "job_search_applications": {"backgroundColor": "#a0eac9", "textColor": "#000000"},  # vert pâle
    "job_search_platforms":    {"backgroundColor": "#c2c2c2", "textColor": "#666666"},  # gris clair
    "newsletters":             {"backgroundColor": "#fce8b3", "textColor": "#666666"},  # jaune pâle
    "spam":                    {"backgroundColor": "#999999", "textColor": "#ffffff"},  # gris foncé
}



LABELS = ["urgent","no_category","spam_","to_delete","professional", "personal", "administrative", "newsletters", "notifications", "job_search_answers", "job_search_applications","job_search_platforms","spam"]



service = get_gmail_service(token_path,credentials_path)

def update_labels_color(service, user_id='me'):
    try:
        existing_labels = service.users().labels().list(userId=user_id).execute().get("labels", [])
        label_id_map = {label["name"]: label["id"] for label in existing_labels}

        for label_name, colors in LABEL_COLOR_MAPPING.items():
            if label_name not in label_id_map:
                print(f"⚠️ Label '{label_name}' non trouvé sur Gmail.")
                continue

            label_id = label_id_map[label_name]
            label_update = {
                "color": {
                    "backgroundColor": colors["backgroundColor"],
                    "textColor": colors["textColor"]
                }
            }

            service.users().labels().update(userId=user_id, id=label_id, body=label_update).execute()
            print(f"✅ Couleur appliquée au label '{label_name}'")

    except HttpError as error:
        print(f"❌ Erreur API Gmail : {error}")
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")

update_labels_color(service)