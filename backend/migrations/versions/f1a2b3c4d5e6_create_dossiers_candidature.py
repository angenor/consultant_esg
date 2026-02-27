"""create_dossiers_candidature

Revision ID: f1a2b3c4d5e6
Revises: effc4cfeb230
Create Date: 2026-02-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'effc4cfeb230'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'dossiers_candidature',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('entreprise_id', sa.Uuid(), nullable=False),
        sa.Column('fonds_id', sa.Uuid(), nullable=False),
        sa.Column('intermediaire_id', sa.Uuid(), nullable=True),
        sa.Column('type_dossier', sa.String(length=30), nullable=False, server_default='complet'),
        sa.Column('documents_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('zip_path', sa.String(length=500), nullable=True),
        sa.Column('statut', sa.String(length=30), nullable=False, server_default='genere'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['entreprise_id'], ['entreprises.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fonds_id'], ['fonds_verts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['intermediaire_id'], ['intermediaires.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('dossiers_candidature')
