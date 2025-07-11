#il s'agit du script qui permet de détecter le type du email; à partir de mots clés 

#Méthode
# On concatène subject + body du mail.
# On passe tout en minuscule + nettoyage.
# On teste les mots-clés par catégorie (regex \bmot\b).
# On compte les occurrences (score) par catégorie.
# On retourne :
# la ou les catégories détectées,
# les scores de match,
# un mini reasoning pour debug.


import sys
import re
from collections import defaultdict
from typing import Dict
project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)

from Exploration.rules_word import TYPE_RULES



# Dictionnaire complet de mots-clés par catégorie


def detect_label(email: Dict[str, str]) -> Dict:
    """
    Détecte le type d'un email à partir du subject et du body, selon une approche mots-clés.
    """
    #we concatenate the subjet and body and we lower everything
    text = (email.get("subject", "") + " " + email.get("body", "")).lower()
    scores = defaultdict(int)
    
    # Parcours des catégories et recherche des mots-clés
    for category, keywords in TYPE_RULES.items():
        for kw in keywords:
            # Regex avec délimiteurs de mots (\b) pour éviter les faux positifs
            # cette ligne sert à etre sur que les mots entiers sont un match. (exemple : car <> cartoon)
            if re.search(rf"\b{re.escape(kw)}\b", text):
                scores[category] += 1

    # Classement par score décroissant
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    if not sorted_scores:
        return {
            "label": "inconnu",
            "scores": {},
            "reasoning": "Aucun mot-clé trouvé"
        }

    # Catégories avec le meilleur score
    top_score = sorted_scores[0][1]
    best_types = [cat for cat, score in sorted_scores if score == top_score]

    return {
        "label": best_types[0] if best_types else "inconnu",
        "scores": dict(scores),
        "reasoning": f"Match mots-clés sur {', '.join(best_types)}"
    }

"""
if __name__ == "__main__":
    email = {
        "subject": "📅 URGENT : réunion client demain à 10h",
        "body": "Bonjour, merci de confirmer votre présence à la réunion avec le prestataire. maman . papa. frere. copain. bar."
    }

    result = detect_type(email)
    print(result)

"""