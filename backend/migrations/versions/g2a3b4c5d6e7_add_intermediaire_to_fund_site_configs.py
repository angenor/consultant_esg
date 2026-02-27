"""add_intermediaire_to_fund_site_configs

Revision ID: g2a3b4c5d6e7
Revises: f1a2b3c4d5e6
Create Date: 2026-02-27 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'g2a3b4c5d6e7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('fund_site_configs', sa.Column(
        'intermediaire_id', sa.String(36),
        sa.ForeignKey('intermediaires.id', ondelete='SET NULL'),
        nullable=True
    ))


def downgrade() -> None:
    op.drop_column('fund_site_configs', 'intermediaire_id')
