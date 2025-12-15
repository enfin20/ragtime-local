import os
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).parent.parent # Racine du projet (rag_local)
OUTPUT_DIR = Path("docs/concat")

# Liste exhaustive des dossiers à scanner
TARGETS = [
    {
        "name": "database", 
        "paths": ["database", "database/models"] # <-- Ajout de models
    },
    {
        "name": "schemas", 
        "paths": ["schemas"]
    },
    {
        "name": "repositories", 
        "paths": ["repositories"]
    },
    {
        "name": "utils", 
        "paths": ["utils"]
    },
    {
        "name": "services_core", 
        "paths": ["services"] # llm.py, ingestion.py...
    },
    {
        "name": "services_chunking", 
        "paths": ["services/chunking", "services/chunking/strategies"] # <-- Ajout des stratégies
    },
    {
        "name": "api", 
        "paths": ["api", "api/routes"] # <-- Ajout des routes
    },
    {
        "name": "scripts", 
        "paths": ["scripts"]
    },
]

IGNORE_DIRS = ["__pycache__", ".venv", "venv", ".git", ".vscode", "logs", "docs", "data"]
IGNORE_FILES = [".DS_Store", "local_database.db", ".env"]

def generate_tree(dir_path: Path, prefix: str = ""):
    output = ""
    try:
        # Trier : Dossiers d'abord, puis fichiers
        items = sorted(list(dir_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
        
        filtered_items = [
            i for i in items 
            if i.name not in IGNORE_DIRS 
            and i.name not in IGNORE_FILES
            and not i.name.endswith(".pyc")
        ]

        for index, item in enumerate(filtered_items):
            is_last = (index == len(filtered_items) - 1)
            connector = "└── " if is_last else "├── "
            output += f"{prefix}{connector}{item.name}\n"

            if item.is_dir():
                extension = "    " if is_last else "│   "
                output += generate_tree(item, prefix + extension)
    except PermissionError:
        pass
    return output

def concat_files():
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("🚀 Début de la concaténation Python (Complète)...\n")

    # 1. Génération Arborescence
    print("--- Génération Arborescence ---")
    tree_str = f"PROJET PYTHON LOCAL\nGénéré le : {datetime.now()}\n\nracine\n"
    tree_str += generate_tree(BASE_DIR)
    
    with open(OUTPUT_DIR / "arborescence.txt", "w", encoding="utf-8") as f:
        f.write(tree_str)
    print("✅ arborescence.txt généré.")

    # 2. Concaténation par groupe
    print("\n--- Concaténation des sources ---")
    
    for target in TARGETS:
        out_file = OUTPUT_DIR / f"{target['name']}.py.txt"
        
        file_count = 0
        content_buffer = f"# ==========================================\n# GROUPE : {target['name']}\n# ==========================================\n\n"

        for rel_path in target['paths']:
            abs_path = BASE_DIR / rel_path
            
            if not abs_path.exists():
                # print(f"⚠️ Chemin introuvable (ignoré) : {rel_path}")
                continue

            # On scanne les fichiers .py dans ce dossier précis
            files = list(abs_path.glob("*.py"))
            files.sort()

            for file_path in files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    
                    relative_name = file_path.relative_to(BASE_DIR)
                    content_buffer += f"\n# ------------------------------------------\n"
                    content_buffer += f"# FICHIER : {relative_name}\n"
                    content_buffer += f"# ------------------------------------------\n"
                    content_buffer += code + "\n"
                    file_count += 1
                except Exception as e:
                    print(f"Erreur lecture {file_path}: {e}")

        if file_count > 0:
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(content_buffer)
            print(f"✅ {target['name']} ({file_count} fichiers)")
        else:
            print(f"ℹ️  {target['name']} (Vide)")

    print("\n🏁 Terminé ! Vérifiez le dossier docs/concat/")

if __name__ == "__main__":
    concat_files()