"""fix: supprimer colonne preference_paiement non prévue dans les specs

Revision ID: 001_fix_preference_paiement
Revises: 
Create Date: 2026-06-10

Cette colonne est présente dans la base PostgreSQL (sans doute
générée par une migration antérieure ou une création manuelle)
mais absente du modèle SQLAlchemy actuel et du cahier d'analyse.
Sa contrainte NOT NULL bloque tout INSERT dans la table assures.
"""

from alembic import op
import sqlalchemy as sa

revision = '001_fix_preference_paiement'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Supprimer la colonne parasite si elle existe
    # (op.drop_column échouerait si elle n'existe pas, d'où le try/except)
    try:
        op.drop_column('assures', 'preference_paiement')
        print("✓ Colonne 'preference_paiement' supprimée de la table 'assures'")
    except Exception as e:
        print(f"  Colonne déjà absente ou erreur ignorée : {e}")


def downgrade() -> None:
    # Recréer la colonne avec une valeur par défaut si on rollback
    op.add_column(
        'assures',
        sa.Column(
            'preference_paiement',
            sa.String(50),
            nullable=False,
            server_default='VIREMENT',
        )
    )
