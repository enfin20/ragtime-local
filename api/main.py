import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.connection import engine
from database.models import Base
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)

# Import des routes
from api.routes import ingest, chat, search, auth

# Configuration Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

# Initialisation DB (Au démarrage)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RAGTime Local API",
    description="API pour Ingestion et Chat RAG avec LLM Local",
    version="1.0.0"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Affiche le corps de la requête reçue et l'erreur de validation
    body = await request.body()
    print(f"\n❌ ERREUR 422 - Validation Failed:")
    print(f"📥 Body reçu : {body.decode('utf-8')}")
    print(f"⚠️ Détail erreur : {exc.errors()}\n")
    return JSONResponse(status_code=422, content={"detail": exc.errors(), "body": body.decode('utf-8')})

# Configuration CORS (Pour autoriser le frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # À restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routes
app.include_router(auth.router, prefix="/ingest", tags=["Auth"])
app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(search.router, prefix="/search", tags=["Debug Search"])

@app.get("/")
def root():
    return {"status": "ok", "message": "RAGTime API is running 🚀"}

if __name__ == "__main__":
    import uvicorn
    # Lancement serveur : host 0.0.0.0 pour être accessible sur le réseau local
    uvicorn.run(app, host="0.0.0.0", port=8000)