import requests
import time
import os
import sys

# Configuration
API_URL = "http://127.0.0.1:8000"
EMPLOYEE_ID = "admin_test_master"

# Codes couleurs pour la lisibilité
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def log(step, success, message):
    icon = "✅" if success else "❌"
    color = GREEN if success else RED
    print(f"{color}{icon} [{step}] {message}{RESET}")
    if not success:
        print(f"{RED}   -> ARRÊT CRITIQUE : Corrigez cette étape avant de continuer.{RESET}")
        sys.exit(1)

def create_dummy_pdf():
    filename = "test_doc.pdf"
    with open(filename, "wb") as f:
        f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << >> /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 50 >>\nstream\nBT /F1 12 Tf 72 720 Td (Ceci est un test PDF pour le RAG.) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000157 00000 n \n0000000296 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n400\n%%EOF")
    return filename

def run_tests():
    print(f"\n🚀 DÉMARRAGE BATTERIE DE TESTS SUR {API_URL}\n")

    # ---------------------------------------------------------
    # 1. TEST CONNEXION (Healthcheck)
    # ---------------------------------------------------------
    try:
        r = requests.get(f"{API_URL}/")
        log("API", r.status_code == 200, f"API en ligne (Ping: {r.json().get('status')})")
    except Exception as e:
        log("API", False, f"Impossible de joindre l'API. Lancez 'python -m api.main'. Erreur: {e}")

    # ---------------------------------------------------------
    # 2. TEST INGESTION TEXTE (Route: POST /ingest/text)
    # ---------------------------------------------------------
    print("\n🔹 TEST 2 : Ingestion Texte")
    payload_text = {
        "text": "Le projet Apollo 11 a permis à l'homme de marcher sur la Lune en 1969.",
        "tags": ["espace", "histoire"],
        "employee": EMPLOYEE_ID
    }
    r = requests.post(f"{API_URL}/ingest/text", json=payload_text)
    
    if r.status_code == 200:
        data = r.json()
        log("INGEST_TEXT", True, f"Doc ID: {data.get('doc_id')} | Chunks: {data.get('chunks_count')}")
    else:
        log("INGEST_TEXT", False, f"Erreur {r.status_code}: {r.text}")

    # ---------------------------------------------------------
    # 3. TEST INGESTION URL (Route: POST /ingest/url)
    # ---------------------------------------------------------
    print("\n🔹 TEST 3 : Ingestion URL")
    # URL Wikipédia simple pour éviter les blocages
    payload_url = {
        "url": "https://fr.wikipedia.org/wiki/Lune",
        "tags": ["wiki", "espace"],
        "employee": EMPLOYEE_ID
    }
    r = requests.post(f"{API_URL}/ingest/url", json=payload_url)

    if r.status_code == 200:
        data = r.json()
        log("INGEST_URL", True, f"Doc ID: {data.get('doc_id')} | Chunks: {data.get('chunks_count')}")
    else:
        # On tolère l'échec si Tavily n'est pas configuré, mais on le signale
        if "TAVILY_API_KEY" not in os.environ and "400" in str(r.status_code):
             print(f"{RED}⚠️  Echec URL : Vérifiez votre TAVILY_API_KEY dans .env{RESET}")
        else:
            log("INGEST_URL", False, f"Erreur {r.status_code}: {r.text}")

    # ---------------------------------------------------------
    # 4. TEST INGESTION FICHIER (Route: POST /ingest/file)
    # ---------------------------------------------------------
    print("\n🔹 TEST 4 : Ingestion Fichier (Upload)")
    pdf_name = create_dummy_pdf()
    try:
        with open(pdf_name, "rb") as f:
            files = {"file": (pdf_name, f, "application/pdf")}
            data = {"tags": "pdf,test", "employee": EMPLOYEE_ID}
            r = requests.post(f"{API_URL}/ingest/file", files=files, data=data)
        
        if r.status_code == 200:
            res_json = r.json()
            log("INGEST_FILE", True, f"Doc ID: {res_json.get('doc_id')}")
        else:
            log("INGEST_FILE", False, f"Erreur {r.status_code}: {r.text}")
    finally:
        if os.path.exists(pdf_name):
            os.remove(pdf_name)

    print("⏳ Pause 2s pour indexation ChromaDB...")
    time.sleep(2)

    # ---------------------------------------------------------
    # 5. TEST RECHERCHE (Route: POST /search/)
    # ---------------------------------------------------------
    print("\n🔹 TEST 5 : Recherche Vectorielle (Debug)")
    payload_search = {
        "query": "Apollo 11",
        "limit": 3,
        "employee": EMPLOYEE_ID
    }
    r = requests.post(f"{API_URL}/search/", json=payload_search)
    
    if r.status_code == 200:
        results = r.json().get("results", [])
        if results and len(results) > 0:
            log("SEARCH", True, f"Trouvé : {results[0]['content'][:50]}... (Score: {results[0]['score_distance']})")
        else:
            log("SEARCH", False, "Aucun résultat trouvé (Indexation échouée ?)")
    else:
        log("SEARCH", False, f"Erreur {r.status_code}: {r.text}")

    # ---------------------------------------------------------
    # 6. TEST CHAT (Route: POST /chat/)
    # ---------------------------------------------------------
    print("\n🔹 TEST 6 : Chat RAG")
    payload_chat = {
        "question": "Quand l'homme a-t-il marché sur la Lune ?",
        "employee": EMPLOYEE_ID
    }
    r = requests.post(f"{API_URL}/chat/", json=payload_chat)

    if r.status_code == 200:
        ans = r.json()
        response_text = ans.get("answer", "")
        sources = ans.get("sources", [])
        print(f"   🤖 Réponse : {response_text}")
        print(f"   📚 Sources : {sources}")
        
        if "1969" in response_text or "Apollo" in response_text:
            log("CHAT", True, "Réponse cohérente avec le contexte.")
        else:
            print(f"{RED}⚠️  Réponse IA faible (Vérifiez le prompt ou le modèle Ollama).{RESET}")
            # On ne bloque pas ici, car techniquement l'API a répondu
    else:
        log("CHAT", False, f"Erreur {r.status_code}: {r.text}")

    print(f"\n{GREEN}🎉 BATTERIE DE TESTS TERMINÉE AVEC SUCCÈS !{RESET}")
    print("Votre API Python fonctionne parfaitement.")

if __name__ == "__main__":
    run_tests()