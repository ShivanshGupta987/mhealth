"""call_sid made non-unique in calls table

Revision ID: 9ff7f9a2dfb1
Revises: f84013e44ee7
Create Date: 2025-10-14 16:37:26.655922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ff7f9a2dfb1'
down_revision: Union[str, Sequence[str], None] = 'f84013e44ee7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
