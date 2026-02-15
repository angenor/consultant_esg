"""add mode_acces to fonds_verts

Revision ID: e7f8a9b0c1d2
Revises: cda774b43b10
Create Date: 2026-02-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, Sequence[str], None] = 'cda774b43b10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('fonds_verts', sa.Column('mode_acces', sa.String(30), nullable=True))


def downgrade() -> None:
    op.drop_column('fonds_verts', 'mode_acces')
