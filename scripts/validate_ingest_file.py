import sys
import os
import time
from dotenv import load_dotenv
from fpdf import FPDF # Pour générer un PDF de test rapidement

# pip install fpdf (juste pour ce script de test) ou créez un fichier manuellement

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine
from database.models import Base
from services.ingestion import ingestion_service
from services.chat import chat_service

def create_dummy_pdf(filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="RAPPORT CONFIDENTIEL - PROJET ORION", ln=1, align="C")
    pdf.cell(200, 10, txt="1. Le budget alloué est de 50 millions d'euros.", ln=2)
    pdf.cell(200, 10, txt="2. Le directeur du projet est M. Vector.", ln=3)
    pdf.output(filename)
    print(f"📄 PDF de test généré : {filename}")

def run_file_test():
    print("🚀 Démarrage Test Ingestion FICHIER (PDF)...")
    Base.metadata.create_all(bind=engine)
    employee_id = "file_tester"
    
    # 1. Génération d'un fichier PDF local
    pdf_path = "test_projet_orion.pdf"
    try:
        create_dummy_pdf(pdf_path)
    except ImportError:
        print("⚠️ 'fpdf' manquant. Installez-le (pip install fpdf) ou créez 'test_projet_orion.pdf' manuellement.")
        return

    # 2. Ingestion
    print(f"\n--- [1] Ingestion du fichier : {pdf_path} ---")
    try:
        # On passe le CHEMIN du fichier
        result = ingestion_service.process_input(
            input_data=pdf_path,
            employee=employee_id,
            tags=["projet", "finance"],
            origin="filesystem"
        )
        print(f"✅ Ingestion Fichier réussie !")
        print(f"   Source détectée : {result['source']}")
        print(f"   Doc ID : {result['doc_id']}")
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return

    # Pause Indexation
    time.sleep(1)

    # 3. Chat
    print("\n--- [2] Vérification RAG sur le PDF ---")
    question = "Quel est le budget du projet Orion et qui est le directeur ?"
    
    answer = chat_service.chat(question, employee_id)
    
    print(f"🤖 Réponse IA :\n{answer['response']}")
    print(f"📚 Sources : {answer['sources']}")

    # Nettoyage
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

if __name__ == "__main__":
    run_file_test()