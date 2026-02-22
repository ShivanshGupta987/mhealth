"""rename flagged_since timestamp to Call_Scheduled_DateTime

Revision ID: 86f18959926f
Revises: 07384d990e9c
Create Date: 2025-12-23 12:51:09.028881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86f18959926f'
down_revision: Union[str, Sequence[str], None] = '07384d990e9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
