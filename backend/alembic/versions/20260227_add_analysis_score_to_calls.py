"""add analysis_score to calls table

Revision ID: 20260227_add_analysis_score
Revises: f122396d2b6a
Create Date: 2026-02-27 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260227_add_analysis_score"
down_revision: Union[str, Sequence[str], None] = "f122396d2b6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "Calls",
        sa.Column("Analysis_Score", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("Calls", "Analysis_Score")
