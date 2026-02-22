"""merge c2f8d7c9ac92 and 20251208_reduce_targets_columns

Revision ID: 1eabcef99b37
Revises: 20251208_reduce_targets_columns, c2f8d7c9ac92
Create Date: 2025-12-08 12:47:30.620654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1eabcef99b37'
down_revision: Union[str, Sequence[str], None] = ('20251208_reduce_targets_columns', 'c2f8d7c9ac92')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
