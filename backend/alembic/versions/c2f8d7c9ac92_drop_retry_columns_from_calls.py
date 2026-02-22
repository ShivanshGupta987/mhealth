"""drop retry-related columns from Calls

Revision ID: c2f8d7c9ac92
Revises: e829344e2164
Create Date: 2025-12-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2f8d7c9ac92"
down_revision: Union[str, Sequence[str], None] = "e829344e2164"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop unused retry columns from Calls."""
    op.drop_column("Calls", "Retries_Count")
    op.drop_column("Calls", "Prev_Attempt_Scheduled_Time")
    op.drop_column("Calls", "End_Time")
    op.drop_column("Calls", "Next_Retry_Time")


def downgrade() -> None:
    """Recreate retry columns on Calls."""
    op.add_column(
        "Calls",
        sa.Column("Next_Retry_Time", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "Calls",
        sa.Column("End_Time", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "Calls",
        sa.Column("Prev_Attempt_Scheduled_Time", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "Calls",
        sa.Column("Retries_Count", sa.Integer(), nullable=True),
    )
