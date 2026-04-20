"""drop legacy exotel tables now owned by twilio_service

Revision ID: 20260415_drop_legacy_tables
Revises: 20260227_add_analysis_score
Create Date: 2026-04-15 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260415_drop_legacy_tables"
down_revision: Union[str, Sequence[str], None] = "20260227_add_analysis_score"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def upgrade() -> None:
    # Drop Exotel-era backend tables that overlap with Twilio service ownership.
    # Order matters because of foreign keys.
    for table_name in ["FlaggedTargets", "Calls", "Targets", "Models", "Emotions"]:
        if _has_table(table_name):
            op.drop_table(table_name)

    # Clean up enum type if it is left behind after dropping Calls.
    op.execute("DROP TYPE IF EXISTS call_status_enum")


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is not supported for legacy Exotel table removal migration."
    )
