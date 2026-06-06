from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.exceptions import (
    validation_exception_handler,
    integrity_error_handler,
    generic_exception_handler,
)
from app.routers import assures, medecins, feuilles_maladie, prescriptions, remboursements

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=(
        "API REST pour le système de gestion de l'organisme de sécurité sociale. "
        "Gestion des assurés, médecins, feuilles de maladie, prescriptions et remboursements."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — autoriser les requêtes depuis le frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handlers d'erreurs globaux
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Inclusion des routers
PREFIX = settings.API_PREFIX
app.include_router(assures.router, prefix=PREFIX)
app.include_router(medecins.router, prefix=PREFIX)
app.include_router(feuilles_maladie.router, prefix=PREFIX)
app.include_router(prescriptions.router, prefix=PREFIX)
app.include_router(remboursements.router, prefix=PREFIX)


@app.get("/", tags=["Santé"])
async def root():
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "statut": "en ligne",
        "documentation": "/docs",
    }


@app.get("/health", tags=["Santé"])
async def health_check():
    return {"statut": "ok"}
