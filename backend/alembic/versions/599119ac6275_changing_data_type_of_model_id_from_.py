"""Changing data type of Model_Id from UUID to string

Revision ID: 599119ac6275
Revises: 40ec0bfb9fa4
Create Date: 2025-09-30 20:51:57.605762

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql # <--- ADD THIS LINE

# revision identifiers, used by Alembic.
revision: str = '599119ac6275'
down_revision: Union[str, Sequence[str], None] = '40ec0bfb9fa4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # 1. DROP the Foreign Key constraint on the 'Calls' table
    op.drop_constraint('Calls_Model_Id_fkey', 'Calls', type_='foreignkey')

    # 2. ALTER DATA TYPES (Change both columns to String(10))
    
    # Change PK in 'Models' table (UUID -> String)
    op.alter_column(
        'Models', 
        'Model_Id',
        existing_type=postgresql.UUID(as_uuid=True),
        type_=sa.String(length=10),
        postgresql_using='CAST("Model_Id" AS VARCHAR(10))',
        existing_nullable=False
    )
    
    # Change FK in 'Calls' table (UUID -> String)
    op.alter_column(
        'Calls', 
        'Model_Id',
        existing_type=postgresql.UUID(as_uuid=True),
        type_=sa.String(length=10),
        postgresql_using='CAST("Model_Id" AS VARCHAR(10))',
        existing_nullable=True
    )

    # 3. RECREATE the Foreign Key constraint
    op.create_foreign_key(
        'Calls_Model_Id_fkey', 
        'Calls', 
        'Models', 
        ['Model_Id'], 
        ['Model_Id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    
    # 1. DROP the Foreign Key constraint on the 'Calls' table
    op.drop_constraint('Calls_Model_Id_fkey', 'Calls', type_='foreignkey')

    # 2. ALTER DATA TYPES (Change both columns back to UUID)
    
    # Change FK in 'Calls' table (String -> UUID)
    op.alter_column(
        'Calls', 
        'Model_Id',
        existing_type=sa.String(length=10),
        type_=postgresql.UUID(as_uuid=True),
        existing_nullable=True,
        postgresql_using='CAST("Model_Id" AS UUID)' 
    )

    # Change PK in 'Models' table (String -> UUID)
    op.alter_column(
        'Models', 
        'Model_Id',
        existing_type=sa.String(length=10),
        type_=postgresql.UUID(as_uuid=True),
        existing_nullable=False,
        postgresql_using='CAST("Model_Id" AS UUID)'
    )
    
    # 3. RECREATE the Foreign Key constraint
    op.create_foreign_key(
        'Calls_Model_Id_fkey', 
        'Calls', 
        'Models', 
        ['Model_Id'], 
        ['Model_Id']
    )