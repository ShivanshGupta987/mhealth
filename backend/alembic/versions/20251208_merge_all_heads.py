"""merge all heads

Revision ID: 20251208_merge_all_heads
Revises: 1eabcef99b37
Create Date: 2025-12-08 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251208_merge_all_heads"
down_revision: Union[str, Sequence[str], None] = "1eabcef99b37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op merge to resolve phantom revision
    pass


def downgrade() -> None:
    # No-op merge rollback
    pass
