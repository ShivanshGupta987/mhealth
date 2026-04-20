"""Rename Duration to Overall_Duration and add Total_Response_Duration column.

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename Duration column to Overall_Duration and add Total_Response_Duration."""
    # Rename Duration to Overall_Duration
    op.alter_column(
        "Twilio_Calls",
        "Duration",
        new_column_name="Overall_Duration",
        existing_type=sa.Integer(),
        existing_nullable=True,
    )
    
    # Add new Total_Response_Duration column
    op.add_column(
        "Twilio_Calls",
        sa.Column(
            "Total_Response_Duration",
            sa.Integer(),
            nullable=True,
            server_default="0",
        ),
    )


def downgrade() -> None:
    """Revert the schema changes."""
    # Drop Total_Response_Duration column
    op.drop_column("Twilio_Calls", "Total_Response_Duration")
    
    # Rename Overall_Duration back to Duration
    op.alter_column(
        "Twilio_Calls",
        "Overall_Duration",
        new_column_name="Duration",
        existing_type=sa.Integer(),
        existing_nullable=True,
    )
