"""create users, chat_sessions, messages, artifacts

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-31 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # --- chat_sessions ---
    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])

    # --- messages ---
    message_role_enum = postgresql.ENUM(
        "user", "assistant", "system", name="message_role"
    )
    message_role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("chat_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("user", "assistant", "system", name="message_role", create_type=False),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["chat_session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_messages_chat_session_id", "messages", ["chat_session_id"])

    # --- artifacts ---
    artifact_type_enum = postgresql.ENUM(
        "text", "code", "markdown", "json", "chart", name="artifact_type"
    )
    artifact_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "artifact_type",
            postgresql.ENUM(
                "text", "code", "markdown", "json", "chart",
                name="artifact_type", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_artifacts_message_id", "artifacts", ["message_id"], unique=True)


def downgrade() -> None:
    op.drop_table("artifacts")
    op.execute("DROP TYPE IF EXISTS artifact_type")

    op.drop_table("messages")
    op.execute("DROP TYPE IF EXISTS message_role")

    op.drop_table("chat_sessions")
    op.drop_table("users")
