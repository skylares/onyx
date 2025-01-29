"""discord thread

Revision ID: 85abec47726e
Revises: 82f52948359d
Create Date: 2025-01-17 16:06:53.031908

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "85abec47726e"
down_revision = "82f52948359d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add discord_thread_id column to chat_session table
    op.add_column(
        "chat_session", sa.Column("discord_thread_id", sa.String(), nullable=True)
    )


def downgrade() -> None:
    # Remove the column if we need to rollback
    op.drop_column("chat_session", "discord_thread_id")
