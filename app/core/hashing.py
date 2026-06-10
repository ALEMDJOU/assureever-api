"""
Hachage des mots de passe avec bcrypt directement.

Remplace passlib[bcrypt] qui est incompatible avec bcrypt >= 4.x
(AttributeError: module 'bcrypt' has no attribute '__about__').

On utilise la librairie `bcrypt` directement — API simple et stable.
"""

import bcrypt


def hash_password(password: str) -> str:
    """Hache un mot de passe en clair. Retourne le hash encodé en UTF-8."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie un mot de passe en clair contre son hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False
