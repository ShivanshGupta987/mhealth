"""adding_stream_sid_to_calls_table

Revision ID: e829344e2164
Revises: 9ff7f9a2dfb1
Create Date: 2025-11-28 11:59:21.743522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e829344e2164'
down_revision: Union[str, Sequence[str], None] = '9ff7f9a2dfb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add Stream_Sid column to Calls table
    op.add_column('Calls', sa.Column('Stream_Sid', sa.String(100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove Stream_Sid column from Calls table
    op.drop_column('Calls', 'Stream_Sid')
