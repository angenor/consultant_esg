"""add type_plan to action_plans

Revision ID: a1b2c3d4e5f6
Revises: fbcfdc6a82d8
Create Date: 2026-02-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fbcfdc6a82d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add nullable column with server default
    op.add_column(
        'action_plans',
        sa.Column('type_plan', sa.String(20), nullable=True, server_default='esg'),
    )

    # 2. Backfill existing rows
    op.execute("UPDATE action_plans SET type_plan = 'carbone' WHERE titre LIKE 'Plan de réduction carbone%'")
    op.execute("UPDATE action_plans SET type_plan = 'esg' WHERE type_plan IS NULL")

    # 3. Make NOT NULL
    op.alter_column('action_plans', 'type_plan', nullable=False)

    # 4. Index for filtered queries
    op.create_index(
        'idx_action_plans_type',
        'action_plans',
        ['entreprise_id', 'type_plan', 'created_at'],
    )


def downgrade() -> None:
    op.drop_index('idx_action_plans_type', table_name='action_plans')
    op.drop_column('action_plans', 'type_plan')
