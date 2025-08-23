"""
Database migration for authentication system
============================================

Alembic migration to add authentication fields and refresh tokens table.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision = "002_authentication_system"
down_revision = "001_market_data_archive"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add authentication system tables and fields.
    """
    # Add password_hash column to users table
    op.add_column(
        "users",
        sa.Column(
            "password_hash", sa.String(length=255), nullable=False, server_default=""
        ),
    )

    # Update user role enum to include new roles
    # First, create new enum type
    new_role_enum = postgresql.ENUM("admin", "premium", "basic", name="userrole_new")
    new_role_enum.create(op.get_bind())

    # Add temporary column with new enum
    op.add_column("users", sa.Column("role_new", new_role_enum, nullable=True))

    # Migrate existing data
    op.execute(
        """
        UPDATE users SET role_new = CASE 
            WHEN role = 'trader' THEN 'premium'::userrole_new
            WHEN role = 'analyst' THEN 'premium'::userrole_new  
            WHEN role = 'viewer' THEN 'basic'::userrole_new
            ELSE 'basic'::userrole_new
        END
    """
    )

    # Drop old column and rename new one
    op.drop_column("users", "role")
    op.alter_column("users", "role_new", new_column_name="role")
    op.alter_column("users", "role", nullable=False)

    # Drop old enum type
    old_role_enum = postgresql.ENUM(name="userrole")
    old_role_enum.drop(op.get_bind())

    # Rename new enum type
    op.execute("ALTER TYPE userrole_new RENAME TO userrole")

    # Create refresh_tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for refresh_tokens
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"], unique=True)
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index("ix_refresh_tokens_is_revoked", "refresh_tokens", ["is_revoked"])

    # Add indexes to users table for authentication
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_is_active", "users", ["is_active"])


def downgrade() -> None:
    """
    Remove authentication system tables and fields.
    """
    # Drop refresh_tokens table
    op.drop_table("refresh_tokens")

    # Drop user indexes
    op.drop_index("ix_users_email", "users")
    op.drop_index("ix_users_is_active", "users")

    # Revert user role enum
    # Create old enum type
    old_role_enum = postgresql.ENUM("trader", "analyst", "viewer", name="userrole_old")
    old_role_enum.create(op.get_bind())

    # Add temporary column with old enum
    op.add_column("users", sa.Column("role_old", old_role_enum, nullable=True))

    # Migrate data back
    op.execute(
        """
        UPDATE users SET role_old = CASE 
            WHEN role = 'admin' THEN 'trader'::userrole_old
            WHEN role = 'premium' THEN 'trader'::userrole_old
            WHEN role = 'basic' THEN 'viewer'::userrole_old
            ELSE 'viewer'::userrole_old
        END
    """
    )

    # Drop new column and rename old one
    op.drop_column("users", "role")
    op.alter_column("users", "role_old", new_column_name="role")
    op.alter_column("users", "role", nullable=False)

    # Drop new enum type
    new_role_enum = postgresql.ENUM(name="userrole")
    new_role_enum.drop(op.get_bind())

    # Rename old enum type
    op.execute("ALTER TYPE userrole_old RENAME TO userrole")

    # Remove password_hash column
    op.drop_column("users", "password_hash")
