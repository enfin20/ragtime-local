import requests
import time
import sys
import json

# Configuration
API_URL = "http://127.0.0.1:8000"
TEST_USER = "admin_test"
TEST_DOC_TEXT = "Le projet secret s'appelle 'Projet Omega'. Il vise à créer une IA quantique d'ici 2030."

def run_test():
    print(f"🚀 Démarrage du Test Fonctionnel sur {API_URL}...\n")

    # ---------------------------------------------------------
    # 1. INGESTION (On pousse la donnée)
    # ---------------------------------------------------------
    print("🔹 [ETAPE 1] Ingestion du document...")
    try:
        res = requests.post(f"{API_URL}/ingest/text", json={
            "text": TEST_DOC_TEXT,
            "tags": ["test", "secret"],
            "employee": TEST_USER
        })
        if res.status_code != 200:
            print(f"   ❌ Erreur API Ingest ({res.status_code}) : {res.text}")
            return
        
        data = res.json()
        print(f"   ✅ Ingestion OK. ID: {data.get('doc_id')} | Chunks créés: {data.get('chunks_count')}")
        
        if data.get('chunks_count') == 0:
            print("   ⚠️  ATTENTION : 0 chunks créés ! Vérifiez 'services/chunking/manager.py'.")
            return

    except Exception as e:
        print(f"   ❌ Exception critique : {e}")
        return

    print("   ⏳ Attente de 2 secondes pour l'indexation...")
    time.sleep(2)

    # ---------------------------------------------------------
    # 2. VERIFICATION SEARCH (On vérifie la présence physique)
    # ---------------------------------------------------------
    print("\n🔹 [ETAPE 2] Vérification Vectorielle (Search)...")
    try:
        # On utilise la route /search que vous avez ajoutée dans api.py
        res = requests.post(f"{API_URL}/search/", json={
            "query": "Omega",
            "limit": 3,
            "employee": TEST_USER
        })
        
        if res.status_code == 200:
            results = res.json().get("results", [])
            found = False
            for r in results:
                if "Omega" in r.get("content", ""):
                    print(f"   ✅ Contenu retrouvé dans Chroma ! (Score: {r.get('score_distance')})")
                    print(f"      Extrait : {r.get('content')[:50]}...")
                    found = True
                    break
            
            if not found:
                print("   ❌ ECHEC : Le document n'est pas remonté par la recherche vectorielle.")
                print(f"      Résultats bruts : {json.dumps(results, indent=2)}")
                return
        else:
            print(f"   ❌ Erreur API Search ({res.status_code}) : {res.text}")
            return

    except Exception as e:
        print(f"   ❌ Erreur lors du test Search : {e}")
        return

    # ---------------------------------------------------------
    # 3. TEST CHAT (On teste l'intelligence)
    # ---------------------------------------------------------
    print("\n🔹 [ETAPE 3] Test du Chat (RAG)...")
    question = "Quel est le nom du projet secret et son but ?"
    try:
        res = requests.post(f"{API_URL}/chat/", json={
            "question": question,
            "employee": TEST_USER
        })
        
        if res.status_code == 200:
            answer = res.json().get("answer", "")
            sources = res.json().get("sources", [])
            
            print(f"   ❓ Question : {question}")
            print(f"   🤖 Réponse  : {answer}\n")
            
            if "Omega" in answer:
                print("   🎉 SUCCÈS TOTAL : Le système fonctionne de bout en bout !")
            else:
                print("   🔸 RESULTAT MITIGÉ : Le document est trouvé mais le LLM ne l'a pas utilisé.")
                print("      -> Vérifiez le Prompt Système dans 'services/chat.py'.")
        else:
            print(f"   ❌ Erreur API Chat ({res.status_code}) : {res.text}")

    except Exception as e:
        print(f"   ❌ Erreur lors du test Chat : {e}")

if __name__ == "__main__":
    run_test()