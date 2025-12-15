import json
import logging

logger = logging.getLogger(__name__)

def robust_json_parse(llm_output: str) -> dict | list | None:
    """
    Extrait un JSON (Objet ou Liste) de manière robuste sans Regex complexes.
    """
    if not llm_output:
        return None

    text = llm_output.strip()

    # 1. Nettoyage basique des balises Markdown ```json ... ```
    if "```" in text:
        lines = text.splitlines()
        # On filtre les lignes qui contiennent ```
        text = "\n".join([l for l in lines if "```" not in l]).strip()

    # 2. Recherche des bornes JSON (Optimisé)
    # On cherche le premier '[' ou '{'
    first_square = text.find('[')
    first_curly = text.find('{')
    
    start_index = -1
    is_array = False

    # Détermination du début (lequel arrive en premier ?)
    if first_square != -1 and first_curly != -1:
        if first_square < first_curly:
            start_index = first_square
            is_array = True
        else:
            start_index = first_curly
    elif first_square != -1:
        start_index = first_square
        is_array = True
    elif first_curly != -1:
        start_index = first_curly
    
    if start_index == -1:
        return None

    # Détermination de la fin correspondante
    end_char = ']' if is_array else '}'
    end_index = text.rfind(end_char)

    if end_index == -1 or end_index < start_index:
        return None

    json_candidate = text[start_index : end_index + 1]

    try:
        return json.loads(json_candidate)
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {e}")
        return None