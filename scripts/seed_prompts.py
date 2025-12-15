import sys
import os
import json

# Path hack
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.connection import engine
from database.models import Base
from repositories.prompt import prompt_repository
from schemas.prompt import PromptCreate

# VOS DONNÉES JSON (Copiées depuis votre fichier)
RAW_PROMPTS_DATA = [
{
    "name": "synthesis_tags",
    "user": "system",
    "prompt": "# RÔLE\nTu es un expert en analyse documentaire.\n\n# MISSION\nAnalyse le document JSON/Texte et génère une synthèse structurée.\n\n# SORTIE (JSON UNIQUEMENT)\n{\n  \"synthesis\": \"Résumé en ANGLAIS de 15 lignes max. Identifie le type (Profil, Entreprise, Article).\",\n  \"suggested_tags\": [\"tag1\", \"tag2\"] (Max 5, anglais, minuscule, sans espace)\n}"
  },
  {
    "name": "agent_rerank",
    "user": "system",
    "prompt": "Tu es un juge de pertinence strict.\nÉvalue les chunks par rapport à la QUESTION : \"{question}\"\n\nCONTEXTE :\n{context}\n\n# RÈGLES DE SCORING (0.0 à 1.0)\n\n1. **BRUIT = 0.0** : Si le chunk est une liste de liens, 'Related Articles', 'See Also', un pied de page, des mentions légales ou une pub.\n2. **CORRESPONDANCE EXACTE = 1.0** : Si la réponse ou les métadonnées (dates, noms) correspondent parfaitement.\n3. **PERTINENT = 0.6 - 0.9** : Le contexte est bon.\n4. **HORS SUJET = 0.1** : Aucun rapport.\n\n# SORTIE (JSON UNIQUEMENT)\n[\n  { \"chunk_index\": 0, \"score\": 0.0 },\n  { \"chunk_index\": 1, \"score\": 0.9 }\n]"
  },
  {
    "name": "chunk_post",
    "user": "system",
    "prompt": "# MISSION\nExtrais les métadonnées de ce post LinkedIn.\n\n# TEXTE\n{text}\n\n# SORTIE (JSON UNIQUEMENT)\n{\n  \"metadata\": {\n    \"name\": \"...\",\n    \"company\": \"...\",\n    \"industry\": \"...\",\n    \"location\": \"...\",\n    \"type\": \"general | experience | education | post\"\n  }\n}"
  },
  {
    "name": "chunk_about",
    "user": "system",
    "prompt": "# MISSION\nExtrais les compétences et infos clés de ce texte 'About'.\n\n# SORTIE (JSON UNIQUEMENT)\n{\n  \"metadata\": {\n    \"hard_skills\": [\"...\"],\n    \"soft_skills\": [\"...\"],\n    \"technologies\": [\"...\"],\n    \"projects\": [\"...\"]\n  }\n}"
  },
  {
    "name": "chunk_hypothetical_questions",
    "user": "system",
    "prompt": "Génère 3 questions courtes auxquelles ce texte répond :\n\n\"\"\"\n${text}\n\"\"\"\n\nFormat : Une question par ligne, sans puce ni numéro."
  },
  {
    "name": "chunk_entities",
    "user": "system",
    "prompt": "# MISSION\nExtrais les entités nommées.\n\nTEXTE:\n{text}\n\n# SORTIE (JSON)\n{\n  \"people\": [{ \"name\": \"...\" }],\n  \"companies\": [{ \"name\": \"...\" }],\n  \"locations\": [{ \"name\": \"...\" }],\n  \"tools\": [{ \"name\": \"...\" }]\n}"
  },
  {
    "name": "graph_extraction",
    "user": "system",
    "prompt": "Extrais les relations (triplets) du texte.\n\n# SORTIE (JSON)\n{\n  \"triplets\": [\n    {\n      \"source\": \"Entité1\",\n      \"source_type\": \"PERSON|COMPANY\",\n      \"relation\": \"VERBE_MAJUSCULE\",\n      \"target\": \"Entité2\",\n      \"target_type\": \"LOCATION|TOOL\"\n    }\n  ]\n}"
  },
    {
    "name": "three-pass",
    "user": "cv@duhamel.xyz",
    "prompt": "Pass 1: a quick skim of what the paper is about.\nPass 2: the main ideas and why they matter.\nPass 3: the deeper details I should pay attention to.\nJE VEUX TES REPONSES EN FRANÇAIS"
  }
]

def seed_prompts():
    print("🚀 Initialisation des Prompts (Seed)...")
    
    # S'assurer que la table existe
    Base.metadata.create_all(bind=engine)
    
    print("🧹 Nettoyage de la table 'prompts' existante...")
    try:
        with engine.connect() as connection:
            connection.execute(text("DELETE FROM prompts"))
            connection.commit()
            print("🗑️ Table vidée avec succès.")
    except Exception as e:
        print(f"⚠️ Attention : Impossible de vider la table (elle est peut-être déjà vide ou le nom diffère) : {e}")

    count = 0
    for p_data in RAW_PROMPTS_DATA:
        try:
            # On ignore l'ID Mongo (_id) s'il est présent, on laisse SQLite gérer
            prompt_in = PromptCreate(
                name=p_data["name"],
                prompt=p_data["prompt"],
                user=p_data["user"],
                description=p_data.get("description")
            )
            prompt_repository.upsert_prompt(prompt_in)
            count += 1
            print(f"✅ Prompt traité : {p_data['name']}")
        except Exception as e:
            print(f"❌ Erreur sur {p_data.get('name')}: {e}")

    print(f"\n🎉 Terminé ! {count} prompts sont maintenant en base SQLite.")

if __name__ == "__main__":
    seed_prompts()