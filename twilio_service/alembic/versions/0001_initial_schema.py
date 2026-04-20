"""Initial schema: Targets, Twilio_Calls, Twilio_Responses

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-10
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── twilio_call_status_enum ──────────────────────────────────────────────
    twilio_call_status_enum = postgresql.ENUM(
        "Call Scheduled",
        "Call Initiated",
        "In Progress",
        "Completed",
        "No Answer",
        "Busy",
        "Failed",
        "Cancelled",
        name="twilio_call_status_enum",
        create_type=True,
    )
    twilio_call_status_enum.create(op.get_bind(), checkfirst=True)

    # ── Targets ──────────────────────────────────────────────────────────────
    op.create_table(
        "Targets",
        sa.Column("Target_Id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("Name", sa.String(255), nullable=False),
        sa.Column("Phone_No", sa.String(20), nullable=False),
        sa.Column("Roll_No", sa.String(50), nullable=True),
        sa.Column("Department", sa.String(100), nullable=True),
        sa.Column("Program", sa.String(100), nullable=True),
        sa.Column(
            "Created_At",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("Phone_No", name="uq_targets_phone"),
        sa.UniqueConstraint("Roll_No", name="uq_targets_roll_no"),
    )

    # ── Twilio_Calls ─────────────────────────────────────────────────────────
    op.create_table(
        "Twilio_Calls",
        sa.Column("Call_Id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("Twilio_Call_Sid", sa.String(64), nullable=True),
        sa.Column(
            "Target_Id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("Targets.Target_Id"),
            nullable=False,
        ),
        sa.Column("Scheduled_Time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("Started_Time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("Ended_Time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "Status",
            postgresql.ENUM(
                "Call Scheduled",
                "Call Initiated",
                "In Progress",
                "Completed",
                "No Answer",
                "Busy",
                "Failed",
                "Cancelled",
                name="twilio_call_status_enum",
                create_type=False,  # already created above
            ),
            nullable=False,
            server_default="Call Scheduled",
        ),
        sa.Column("Total_Questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("Questions_Answered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("Duration", sa.Integer(), nullable=True),
        sa.Column("Overall_Sentiment", sa.String(32), nullable=True),
        sa.Column("Overall_Sentiment_Score", sa.Float(), nullable=True),
        sa.Column(
            "Created_At",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "Target_Id", "Scheduled_Time", name="uq_twilio_target_scheduled_time"
        ),
    )
    op.create_index("ix_twilio_calls_sid", "Twilio_Calls", ["Twilio_Call_Sid"])

    # ── Twilio_Responses ─────────────────────────────────────────────────────
    op.create_table(
        "Twilio_Responses",
        sa.Column("Response_Id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "Call_Id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("Twilio_Calls.Call_Id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("Question_Index", sa.Integer(), nullable=False),
        sa.Column("Question_Text", sa.Text(), nullable=False),
        sa.Column("Response_Type", sa.String(8), nullable=False),
        sa.Column("Response_Value", sa.Text(), nullable=True),
        sa.Column("Response_Label", sa.String(64), nullable=True),
        sa.Column("Recording_Sid", sa.String(64), nullable=True),
        sa.Column("Recording_Duration", sa.Integer(), nullable=True),
        sa.Column("Sentiment_Label", sa.String(32), nullable=True),
        sa.Column("Sentiment_Score", sa.Float(), nullable=True),
        sa.Column(
            "Responded_At",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "Call_Id", "Question_Index", name="uq_twilio_call_question"
        ),
    )
    op.create_index("ix_twilio_responses_call", "Twilio_Responses", ["Call_Id"])


def downgrade() -> None:
    op.drop_table("Twilio_Responses")
    op.drop_table("Twilio_Calls")
    op.drop_table("Targets")

    bind = op.get_bind()
    sa.Enum(name="twilio_call_status_enum").drop(bind, checkfirst=True)
