"""Reduce Targets columns to minimal fields

Revision ID: 20251208_reduce_targets_columns
Revises: 02a0367389f3
Create Date: 2025-12-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_column(table, column)


# revision identifiers, used by Alembic.
revision: str = "20251208_reduce_targets_columns"
down_revision: Union[str, Sequence[str], None] = "02a0367389f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Roll_No and simplify department to plain string
    op.add_column("Targets", sa.Column("Roll_No", sa.String(), nullable=True))
    op.create_unique_constraint("uq_targets_roll_no", "Targets", ["Roll_No"])

    op.alter_column(
        "Targets",
        "Department_Name",
        existing_type=sa.Enum(
            "Computer Science",
            "Mechanical",
            "Chemical",
            "Civil",
            "Biological",
            "Electrical",
            "Chemistry",
            "Mathematics",
            "Physics",
            "Earth Sciences",
            "Humanities and Social Sciences",
            name="department_name_enum",
        ),
        type_=sa.String(),
        nullable=True,
        existing_nullable=True,
    )

    # Drop now-unused columns
    for col in [
        "Street",
        "City",
        "State",
        "Zip_Code",
        "Address",
        "Phone_No",
        "Batch",
        "Semester",
    ]:
        if _has_column("Targets", col):
            op.drop_column("Targets", col)

    # Clean up enum type if using PostgreSQL
    try:
        op.execute("DROP TYPE IF EXISTS department_name_enum")
    except Exception:
        pass


def downgrade() -> None:
    # Recreate dropped columns (as nullable to avoid data issues)
    op.add_column("Targets", sa.Column("Semester", sa.Integer(), nullable=True))
    op.add_column("Targets", sa.Column("Batch", sa.Integer(), nullable=True))
    op.add_column("Targets", sa.Column("Phone_No", sa.String(), nullable=True))
    op.add_column("Targets", sa.Column("Address", sa.String(), nullable=True))
    op.add_column("Targets", sa.Column("Zip_Code", sa.String(), nullable=True))
    op.add_column("Targets", sa.Column("State", sa.String(), nullable=True))
    op.add_column("Targets", sa.Column("City", sa.String(), nullable=True))
    op.add_column("Targets", sa.Column("Street", sa.String(), nullable=True))

    op.alter_column(
        "Targets",
        "Department_Name",
        existing_type=sa.String(),
        type_=sa.Enum(
            "Computer Science",
            "Mechanical",
            "Chemical",
            "Civil",
            "Biological",
            "Electrical",
            "Chemistry",
            "Mathematics",
            "Physics",
            "Earth Sciences",
            "Humanities and Social Sciences",
            name="department_name_enum",
        ),
        nullable=True,
        existing_nullable=True,
    )

    op.drop_constraint("uq_targets_roll_no", "Targets", type_="unique")
    op.drop_column("Targets", "Roll_No")
