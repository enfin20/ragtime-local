from fastapi import APIRouter, HTTPException
from repositories.chunk import chunk_repository
from schemas.api import SearchRequest

router = APIRouter()

@router.post("/", summary="Recherche vectorielle brute (Debug)")
async def search_vector(request: SearchRequest):
    try:
        # On appelle le repository directement
        results = chunk_repository.search(
            query=request.query,
            employee=request.employee,
            limit=request.limit
        )
        
        # On reformate pour la lisibilité
        clean_results = []
        if results['ids']:
            for i, id_val in enumerate(results['ids'][0]):
                clean_results.append({
                    "id": id_val,
                    "score_distance": results['distances'][0][i] if 'distances' in results else "N/A",
                    "content": results['documents'][0][i], # <--- C'est ça qu'on veut vérifier !
                    "metadata": results['metadatas'][0][i]
                })
        
        return {"count": len(clean_results), "results": clean_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))