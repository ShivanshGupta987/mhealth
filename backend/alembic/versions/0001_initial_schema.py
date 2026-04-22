"""Initial schema – all tables in the public schema.

Revision ID: 0001
Revises:
Create Date: 2026-04-22

Creates every table owned by this service:
  Backend tables  : Targets, Calls, Emotions, Models, Admins,
                    Password_Reset_Tokens, Error_Logs, FlaggedTargets
  Twilio tables   : Twilio_Targets, Twilio_Calls, Twilio_Responses

Deploying on an existing database
----------------------------------
If the DB already has tables from previous migrations (old revision hash
in alembic_version), clear it first so alembic can run this migration:

    alembic stamp --purge 0001        # or:  DELETE FROM alembic_version;
    alembic upgrade head

The upgrade() function is idempotent — it skips tables that already exist,
so running it against an existing DB only creates the missing ones.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa_inspect(bind).get_table_names())

    # ── ENUM types ────────────────────────────────────────────────────────────

    call_status_enum = postgresql.ENUM(
        "Call Scheduled",
        "failed",
        "busy",
        "no-answer",
        "Message Not Conveyed",
        "Message Conveyed But Not Processed",
        "Message Conveyed And Processed",
        name="call_status_enum",
        create_type=True,
    )
    call_status_enum.create(op.get_bind(), checkfirst=True)

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

    # ── Backend tables ────────────────────────────────────────────────────────

    if "Targets" not in existing:
        op.create_table(
            "Targets",
            sa.Column("Target_Id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("Name", sa.String(), nullable=False),
            sa.Column("Roll_No", sa.String(), unique=True, nullable=False),
            sa.Column("Phone_No", sa.String(), unique=True, nullable=True),
            sa.Column("Department_Name", sa.String(), nullable=False),
            sa.Column("Program", sa.String(), nullable=False),
        )

    if "Emotions" not in existing:
        op.create_table(
            "Emotions",
            sa.Column("Emotion_Id", sa.String(10), primary_key=True),
            sa.Column("Emotion", sa.String(20), unique=True),
        )

    if "Models" not in existing:
        op.create_table(
            "Models",
            sa.Column("Model_Id", sa.String(10), primary_key=True),
            sa.Column("Model_Name", sa.String()),
            sa.Column("Model_Version", sa.String()),
            sa.Column("Model_Details", sa.Text()),
        )

    if "Calls" not in existing:
        op.create_table(
            "Calls",
            sa.Column("Call_Id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("Call_Sid", sa.String(100), nullable=True),
            sa.Column(
                "Target_Id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("Targets.Target_Id"),
            ),
            sa.Column("Model_Id", sa.String(10), sa.ForeignKey("Models.Model_Id")),
            sa.Column("Scheduled_Time", sa.DateTime(timezone=True)),
            sa.Column("Started_Time", sa.DateTime(timezone=True)),
            sa.Column(
                "Emotion_Id",
                sa.String(10),
                sa.ForeignKey("Emotions.Emotion_Id"),
                nullable=True,
            ),
            sa.Column(
                "Status",
                postgresql.ENUM(
                    "Call Scheduled",
                    "failed",
                    "busy",
                    "no-answer",
                    "Message Not Conveyed",
                    "Message Conveyed But Not Processed",
                    "Message Conveyed And Processed",
                    name="call_status_enum",
                    create_type=False,
                ),
            ),
            sa.Column("Duration", sa.Integer()),
            sa.Column("Recording_Url", sa.String(512), nullable=True),
            sa.Column("Analysis_Score", sa.Float(), nullable=True),
            sa.UniqueConstraint("Target_Id", "Scheduled_Time", name="uq_target_scheduled_time"),
        )

    if "Admins" not in existing:
        op.create_table(
            "Admins",
            sa.Column("Admin_Id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("Email", sa.String(255), unique=True),
            sa.Column("Password", sa.String(255)),
        )

    if "Password_Reset_Tokens" not in existing:
        op.create_table(
            "Password_Reset_Tokens",
            sa.Column("Token_Id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "Admin_Id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("Admins.Admin_Id"),
                nullable=False,
            ),
            sa.Column("Token", sa.String(255), unique=True, nullable=False),
            sa.Column("Created_At", sa.DateTime(timezone=True)),
            sa.Column("Expires_At", sa.DateTime(timezone=True), nullable=False),
            sa.Column("Used", sa.Integer(), server_default="0"),
        )

    if "Error_Logs" not in existing:
        op.create_table(
            "Error_Logs",
            sa.Column("Logs_Id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("Timestamp", sa.DateTime(timezone=True)),
            sa.Column("Error_Type", sa.String()),
            sa.Column("Error_Message", sa.Text()),
        )

    if "FlaggedTargets" not in existing:
        op.create_table(
            "FlaggedTargets",
            sa.Column("Flag_Id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "Target_Id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("Targets.Target_Id"),
                nullable=False,
            ),
            sa.Column("Call_Scheduled_DateTime", sa.DateTime(timezone=True)),
        )

    # ── Twilio tables ─────────────────────────────────────────────────────────

    if "Twilio_Targets" not in existing:
        op.create_table(
            "Twilio_Targets",
            sa.Column("Target_Id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("Name", sa.String(255), nullable=False),
            sa.Column("Phone_No", sa.String(20), unique=True, nullable=False),
            sa.Column("Roll_No", sa.String(50), unique=True, nullable=True),
            sa.Column("Department", sa.String(100), nullable=True),
            sa.Column("Program", sa.String(100), nullable=True),
            sa.Column(
                "Created_At",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    if "Twilio_Calls" not in existing:
        op.create_table(
            "Twilio_Calls",
            sa.Column("Call_Id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("Twilio_Call_Sid", sa.String(64), nullable=True),
            sa.Column(
                "Target_Id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("Twilio_Targets.Target_Id"),
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
                    create_type=False,
                ),
                nullable=False,
                server_default="Call Scheduled",
            ),
            sa.Column("Total_Questions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("Questions_Answered", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("Overall_Duration", sa.Integer(), nullable=True),
            sa.Column("Total_Response_Duration", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("Depression_Risk", sa.Integer(), nullable=True),
            sa.Column("Depression_Risk_Probability", sa.Float(), nullable=True),
            sa.Column("Depression_Risk_Level", sa.String(32), nullable=True),
            sa.Column("Depression_Risk_Confidence", sa.Float(), nullable=True),
            sa.Column("Depression_Analysis_Timestamp", sa.DateTime(timezone=True), nullable=True),
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

    if "Twilio_Responses" not in existing:
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
            sa.Column("TwilioRecordingUrl", sa.Text(), nullable=True),
            sa.Column("MinIORecordingUrl", sa.Text(), nullable=True),
            sa.Column("Analysis_Score", sa.Float(), nullable=True),
            sa.Column(
                "Responded_At",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.UniqueConstraint("Call_Id", "Question_Index", name="uq_twilio_call_question"),
        )
        op.create_index("ix_twilio_responses_call", "Twilio_Responses", ["Call_Id"])


def downgrade() -> None:
    op.drop_index("ix_twilio_responses_call", table_name="Twilio_Responses")
    op.drop_table("Twilio_Responses")
    op.drop_index("ix_twilio_calls_sid", table_name="Twilio_Calls")
    op.drop_table("Twilio_Calls")
    op.drop_table("Twilio_Targets")
    op.drop_table("FlaggedTargets")
    op.drop_table("Error_Logs")
    op.drop_table("Password_Reset_Tokens")
    op.drop_table("Admins")
    op.drop_table("Calls")
    op.drop_table("Models")
    op.drop_table("Emotions")
    op.drop_table("Targets")

    bind = op.get_bind()
    sa.Enum(name="twilio_call_status_enum").drop(bind, checkfirst=True)
    sa.Enum(name="call_status_enum").drop(bind, checkfirst=True)
