"""migration

Revision ID: 82f52948359d
Revises: 027381bce97c
Create Date: 2025-01-17 11:15:22.751328

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from onyx.db.models import EncryptedString


# revision identifiers, used by Alembic.
revision = "82f52948359d"
down_revision = "027381bce97c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create discord_bot table
    op.create_table(
        "discord_bot",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("discord_bot_token", EncryptedString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("discord_bot_token"),
    )

    # Create discord_channel_config table
    op.create_table(
        "discord_channel_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("discord_bot_id", sa.Integer(), nullable=False),
        sa.Column("persona_id", sa.Integer(), nullable=True),
        sa.Column("channel_config", postgresql.JSONB(), nullable=False),
        sa.Column(
            "enable_auto_filters", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.ForeignKeyConstraint(
            ["discord_bot_id"],
            ["discord_bot.id"],
        ),
        sa.ForeignKeyConstraint(
            ["persona_id"],
            ["persona.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create discord_channel_config__standard_answer_category table
    op.create_table(
        "discord_channel_config__standard_answer_category",
        sa.Column("discord_channel_config_id", sa.Integer(), nullable=False),
        sa.Column("standard_answer_category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["discord_channel_config_id"],
            ["discord_channel_config.id"],
        ),
        sa.ForeignKeyConstraint(
            ["standard_answer_category_id"],
            ["standard_answer_category.id"],
        ),
        sa.PrimaryKeyConstraint(
            "discord_channel_config_id", "standard_answer_category_id"
        ),
    )


def downgrade() -> None:
    # Drop tables in reverse order of creation to handle foreign key constraints
    op.drop_table("discord_channel_config__standard_answer_category")
    op.drop_table("discord_channel_config")
    op.drop_table("discord_bot")
