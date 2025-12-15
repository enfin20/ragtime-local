import json
import logging
import re

logger = logging.getLogger(__name__)

def robust_json_parse(llm_output: str) -> dict | list | None:
    """
    Tente d'extraire un JSON valide d'une réponse LLM, même si elle contient du markdown.
    """
    if not llm_output:
        return None

    try:
        # 1. Tentative directe
        return json.loads(llm_output)
    except json.JSONDecodeError:
        pass

    # 2. Extraction du bloc Markdown ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", llm_output, re.IGNORECASE)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # 3. Extraction brutale entre la première { et la dernière }
    try:
        start = llm_output.find("{")
        end = llm_output.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = llm_output[start:end+1]
            return json.loads(json_str)
    except Exception as e:
        logger.error(f"Failed to parse JSON from LLM output: {e}")
    
    return None