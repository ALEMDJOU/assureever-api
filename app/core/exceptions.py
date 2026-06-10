from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "champ": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Erreur de validation", "erreurs": errors},
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    Capture les violations de contraintes PostgreSQL et expose
    la contrainte exacte qui échoue (en dev) pour faciliter le diagnostic.
    """
    import logging
    logger = logging.getLogger("uvicorn.error")

    # exc.orig est l'exception asyncpg sous-jacente — elle contient
    # le nom de la contrainte et le détail de la violation
    orig = getattr(exc, "orig", None)
    constraint = getattr(orig, "constraint_name", None) or ""
    detail_pg  = getattr(orig, "detail", None) or str(orig or exc)

    # Log serveur complet pour le diagnostic
    logger.error(f"IntegrityError — contrainte: {constraint!r} — détail: {detail_pg}")

    # Message utilisateur ciblé selon la contrainte
    messages = {
        "assures_numero_assure_key": "Ce numéro d'assuré existe déjà. Réessayez.",
        "users_email_key":           "Cette adresse email est déjà utilisée.",
        "medecins_matricule_key":    "Ce matricule de médecin existe déjà.",
    }
    message = messages.get(
        constraint,
        f"Conflit de données : un enregistrement similaire existe déjà"
        + (f" (contrainte : {constraint})" if constraint else ""),
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": message, "contrainte": constraint or None},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erreur interne du serveur"},
    )
