"""Add depression risk prediction columns to TwilioCalls

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    # Add depression risk columns to TwilioCalls table
    op.add_column('Twilio_Calls', sa.Column('Depression_Risk', sa.Integer(), nullable=True))
    op.add_column('Twilio_Calls', sa.Column('Depression_Risk_Probability', sa.Float(), nullable=True))
    op.add_column('Twilio_Calls', sa.Column('Depression_Risk_Level', sa.String(32), nullable=True))
    op.add_column('Twilio_Calls', sa.Column('Depression_Risk_Confidence', sa.Float(), nullable=True))
    op.add_column('Twilio_Calls', sa.Column('Depression_Analysis_Timestamp', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    # Remove depression risk columns from TwilioCalls table
    op.drop_column('Twilio_Calls', 'Depression_Analysis_Timestamp')
    op.drop_column('Twilio_Calls', 'Depression_Risk_Confidence')
    op.drop_column('Twilio_Calls', 'Depression_Risk_Level')
    op.drop_column('Twilio_Calls', 'Depression_Risk_Probability')
    op.drop_column('Twilio_Calls', 'Depression_Risk')
