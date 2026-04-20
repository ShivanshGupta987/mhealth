"""Replace sentiment fields with generic analysis score

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    # Add new generic score column (responses only)
    op.add_column("Twilio_Responses", sa.Column("Analysis_Score", sa.Float(), nullable=True))

    # Migrate existing response-level sentiment score values into Analysis_Score
    op.execute(
        'UPDATE "Twilio_Responses" SET "Analysis_Score" = "Sentiment_Score" '
        'WHERE "Sentiment_Score" IS NOT NULL'
    )

    # Drop old sentiment-specific columns
    op.drop_column("Twilio_Calls", "Overall_Sentiment")
    op.drop_column("Twilio_Calls", "Overall_Sentiment_Score")
    op.drop_column("Twilio_Responses", "Sentiment_Label")
    op.drop_column("Twilio_Responses", "Sentiment_Score")


def downgrade():
    # Recreate old sentiment-specific columns
    op.add_column("Twilio_Responses", sa.Column("Sentiment_Score", sa.Float(), nullable=True))
    op.add_column("Twilio_Responses", sa.Column("Sentiment_Label", sa.String(32), nullable=True))
    op.add_column("Twilio_Calls", sa.Column("Overall_Sentiment_Score", sa.Float(), nullable=True))
    op.add_column("Twilio_Calls", sa.Column("Overall_Sentiment", sa.String(32), nullable=True))

    # Restore response-level score values from Analysis_Score where possible
    op.execute(
        'UPDATE "Twilio_Responses" SET "Sentiment_Score" = "Analysis_Score" '
        'WHERE "Analysis_Score" IS NOT NULL'
    )

    # Drop new generic score column
    op.drop_column("Twilio_Responses", "Analysis_Score")
