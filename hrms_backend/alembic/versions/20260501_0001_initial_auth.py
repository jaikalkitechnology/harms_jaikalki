"""Initial auth tables

Revision ID: 20260501_0001
Revises:
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(96), nullable=False, unique=True),
        sa.Column("code", sa.String(16), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("head_id", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "designations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(96), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("level", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "department_id",
            sa.Integer,
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(191), nullable=False, unique=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(128), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_admin_portal", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("mfa_enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("mfa_secret", sa.String(64), nullable=True),
        sa.Column(
            "designation_id",
            sa.Integer,
            sa.ForeignKey("designations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("last_login_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_phone", "users", ["phone"])

    op.create_foreign_key(
        "fk_departments_head_id_users",
        source_table="departments",
        referent_table="users",
        local_cols=["head_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("level", sa.Integer, nullable=False, server_default="1"),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(96), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(32), nullable=False, server_default="general"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "role_id",
            sa.Integer,
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "permission_id",
            sa.Integer,
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
        **_TABLE_KW,
    )

    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role_id",
            sa.Integer,
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assigned_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
        **_TABLE_KW,
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("jti", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("revoked", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("ip", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_jti", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_constraint("fk_departments_head_id_users", "departments", type_="foreignkey")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("designations")
    op.drop_table("departments")
