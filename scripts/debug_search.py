import requests
import json

def debug_search():
    url = "http://127.0.0.1:8000/search/"
    payload = {
        "query": "Goldorak",
        "employee": "admin_ui",
        "limit": 3
    }

    print(f"🔍 Recherche brute sur : {url}")
    try:
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ {data['count']} résultats trouvés.\n")
            for res in data['results']:
                print(f"--- Score: {res['score_distance']} ---")
                print(f"CONTENU : {res['content']}")
                print(f"METADATA : {res['metadata']}\n")
        else:
            print(f"❌ Erreur {r.status_code} : {r.text}")
    except Exception as e:
        print(f"❌ Erreur connexion : {e}")

if __name__ == "__main__":
    debug_search()