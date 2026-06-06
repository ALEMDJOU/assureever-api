# Sécurité Sociale API

API REST FastAPI pour le système de gestion de l'organisme de sécurité sociale.

## Stack technique

| Composant | Technologie |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Base de données | PostgreSQL |
| Validation | Pydantic v2 |
| Auth | JWT (NextAuth.js compatible) |
| PDF | ReportLab |
| Déploiement | Railway |

## Architecture

```
app/
├── core/           → Configuration, sécurité, exceptions
├── models/         → Modèles SQLAlchemy (tables)
├── schemas/        → Schémas Pydantic (validation I/O)
├── services/       → Logique métier
├── routers/        → Endpoints REST
└── main.py         → Point d'entrée
```

## Installation

### Prérequis
- Python 3.12+
- PostgreSQL 16+

### Développement local

```bash
# Cloner le dépôt
git clone https://github.com/ALEMDJOU/securite-sociale-api.git
cd securite-sociale-api

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# Appliquer les migrations
alembic upgrade head

# Lancer le serveur
uvicorn app.main:app --reload
```

### Via Docker Compose

```bash
docker-compose up -d
```

L'API sera accessible sur `http://localhost:8000`.

## Documentation

| Interface | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health check | http://localhost:8000/health |

## Endpoints

### Assurés (`/api/v1/assures`) — Rôle : ASSUREUR
| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/` | Lister les assurés (pagination + recherche) |
| POST | `/` | Inscrire un nouvel assuré |
| GET | `/{id}` | Fiche d'un assuré |
| PUT | `/{id}/medecin-traitant` | Enregistrer le médecin traitant |

### Médecins (`/api/v1/medecins`) — Rôle : ASSUREUR / MEDECIN
| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/` | Lister les médecins (filtre par type) |
| POST | `/` | Enregistrer un médecin |
| GET | `/{id}` | Fiche d'un médecin |

### Feuilles de maladie (`/api/v1/feuilles-maladie`)
| Méthode | Endpoint | Description | Rôle |
|---|---|---|---|
| GET | `/assure/{id}` | Toutes les feuilles d'un assuré | ASSUREUR/MEDECIN |
| GET | `/assure/{id}/en-attente` | Feuilles à rembourser | ASSUREUR |
| POST | `/` | Enregistrer une feuille | MEDECIN |
| PATCH | `/{id}` | Compléter une feuille | ASSUREUR |

### Prescriptions (`/api/v1/prescriptions`) — Rôle : MEDECIN
| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/medicament` | Prescrire un médicament |
| POST | `/consultation-specialiste` | Prescrire chez un spécialiste |

### Remboursements (`/api/v1/remboursements`) — Rôle : ASSUREUR
| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/assure/{id}` | Historique des remboursements |
| POST | `/` | Effectuer un remboursement |
| GET | `/{id}/facture` | Télécharger la facture PDF |

## Règles métier

- **Taux de remboursement** : 100% pour un médecin généraliste, 80% pour un spécialiste
- **Médecin traitant** : Seul un médecin GENERALISTE peut être désigné comme médecin traitant
- **Contrôle de doublon** : Vérification nom + prénom + date de naissance à l'inscription
- **Statuts feuille de maladie** : EN_ATTENTE → COMPLETE → REMBOURSEE

## Variables d'environnement

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/securite_sociale
NEXTAUTH_SECRET=votre-secret-32-caracteres-minimum
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

## Déploiement Railway

1. Connecter le dépôt GitHub à Railway
2. Configurer les variables d'environnement dans Railway
3. Railway détecte automatiquement le `Dockerfile`
4. Lancer la migration : `alembic upgrade head` (via Railway CLI ou la console)

## Migrations

```bash
# Créer une nouvelle migration
alembic revision --autogenerate -m "description"

# Appliquer les migrations
alembic upgrade head

# Revenir en arrière
alembic downgrade -1
```

## Auteurs

Projet tutoré 3GI — Conception des Systèmes d'Information  
Supervisé par Dr. Anne Marie CHANA et Dr. Jaures Styve KAMENI
