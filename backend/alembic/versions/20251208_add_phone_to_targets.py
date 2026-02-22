"""Add phone number to Targets

Revision ID: 20251208_add_phone_to_targets
Revises: 20251208_merge_all_heads
Create Date: 2025-12-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251208_add_phone_to_targets"
down_revision: Union[str, Sequence[str], None] = "20251208_merge_all_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    bind = op.get_bind()
    return sa.inspect(bind)


def _has_column(table: str, column: str) -> bool:
    inspector = _inspector()
    cols = inspector.get_columns(table)
    return any(col.get("name") == column for col in cols)


def upgrade() -> None:
    if not _has_column("Targets", "Phone_No"):
        op.add_column("Targets", sa.Column("Phone_No", sa.String(), nullable=True))

    inspector = _inspector()
    uniques = {uc.get("name") for uc in inspector.get_unique_constraints("Targets")}
    if "uq_targets_phone_no" not in uniques:
        op.create_unique_constraint("uq_targets_phone_no", "Targets", ["Phone_No"])


def downgrade() -> None:
    # drop unique then column
    try:
        op.drop_constraint("uq_targets_phone_no", "Targets", type_="unique")
    except Exception:
        pass
    if _has_column("Targets", "Phone_No"):
        op.drop_column("Targets", "Phone_No")
