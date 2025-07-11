# méthode 2 : Similarité sémantique via embeddings + FAISS
# detect_type_faiss.py

import sys
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict
import os
#pour desactiver le parallélisme car cela peut causer des ennuis.
os.environ["TOKENIZERS_PARALLELISM"] = "false"

project_path = '/Users/focus_profond/GIT_repo/email_assistant'
if project_path not in sys.path:
    sys.path.append(project_path)

# Prototypes par catégorie
#from Config.embedded_label import LABELS, PROTOTYPES
from Config.classification_label import LABELS, PROTOTYPES
from Config.config import model_sentencetransformer



# Chargement du modèle
model = SentenceTransformer(model_sentencetransformer)

# Embeddings prototypes
#The purpose of this code is to prepare a set of text examples and their corresponding embeddings for further use in NLP tasks. 
# By converting text into embeddings, it becomes easier to perform tasks such as: classification, clustering, semantic search.
prototype_texts = []
prototype_labels = []

for label, examples in PROTOTYPES.items():
    #prototype_texts.extend(examples)
    #prototype_labels.extend([label]*len(examples))
    for example in examples:
        prototype_texts.append(example)
        prototype_labels.append(label)

prototype_embeddings = model.encode(prototype_texts)

def detect_label_semantic(email: Dict[str, str]) -> Dict:
    """
    Classe un email par type via similarité sémantique (cosine) avec des exemples prototypes
    """
    #text = (email.get("subject", "") + " " + email.get("body", "")).strip()
    #print(type(email), email)
    text=((email['subject'])+' '+(email['body'])).strip()
    if not text:
        return {"label": "inconnu", "score": 0.0,"delta":0.0, "match": None}

    emb = model.encode([text])
    sims = cosine_similarity(emb, prototype_embeddings)[0]
    
    # Tri décroissant des scores et index associés
    sorted_indices = np.argsort(sims)[::-1]
    top1_idx = sorted_indices[0]
    top2_idx = sorted_indices[1] if len(sorted_indices) > 1 else None

    top1_score = float(sims[top1_idx])
    top2_score = float(sims[top2_idx]) if top2_idx is not None else 0.0
    delta = top1_score - top2_score


    return {
       "label": prototype_labels[top1_idx],
        "score": round(top1_score, 3),
        "score2":round(top2_score,3),
        "label2":prototype_labels[top2_idx],
        "delta": round(delta, 3),
        "match": prototype_texts[top1_idx],
        "reasoning": f"Plus proche de : \"{prototype_texts[top1_idx][:60]}...\""
    }


