"""Add dual recording URLs (Twilio + MinIO) to Twilio_Responses

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-17

Adds two new columns:
- TwilioRecordingUrl: stores original Twilio URL (permanent, survives storage migration)
- MinIORecordingUrl: stores MinIO URL when archived (optional)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "Twilio_Responses",
        sa.Column("TwilioRecordingUrl", sa.Text(), nullable=True),
    )
    op.add_column(
        "Twilio_Responses",
        sa.Column("MinIORecordingUrl", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("Twilio_Responses", "MinIORecordingUrl")
    op.drop_column("Twilio_Responses", "TwilioRecordingUrl")
