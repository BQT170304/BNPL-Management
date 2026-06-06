"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-06-06

"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "financial_profiles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("salary", sa.BigInteger(), nullable=False),
        sa.Column("secondary", sa.BigInteger(), nullable=False),
        sa.Column("avg_bonus_monthly", sa.BigInteger(), nullable=False),
        sa.Column("passive", sa.BigInteger(), nullable=False),
        sa.Column("emergency_fund", sa.BigInteger(), nullable=False),
        sa.Column("risk", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("classification", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["financial_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expenses_profile_id", "expenses", ["profile_id"])
    op.create_table(
        "debts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("monthly_payment", sa.BigInteger(), nullable=False),
        sa.Column("balance", sa.BigInteger(), nullable=True),
        sa.Column("apr", sa.Float(), nullable=False),
        sa.Column("months_remaining", sa.Integer(), nullable=True),
        sa.Column("debt_type", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["financial_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_debts_profile_id", "debts", ["profile_id"])
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("value", sa.BigInteger(), nullable=False),
        sa.Column("liquidity", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["financial_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assets_profile_id", "assets", ["profile_id"])
    op.create_table(
        "goals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("target_amount", sa.BigInteger(), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("savings_allocated", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["financial_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goals_profile_id", "goals", ["profile_id"])


def downgrade() -> None:
    op.drop_index("ix_goals_profile_id", table_name="goals")
    op.drop_table("goals")
    op.drop_index("ix_assets_profile_id", table_name="assets")
    op.drop_table("assets")
    op.drop_index("ix_debts_profile_id", table_name="debts")
    op.drop_table("debts")
    op.drop_index("ix_expenses_profile_id", table_name="expenses")
    op.drop_table("expenses")
    op.drop_table("financial_profiles")
