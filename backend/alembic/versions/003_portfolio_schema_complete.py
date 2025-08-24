"""Expand portfolio schema with complete financial fields

Revision ID: 003_portfolio_schema_complete  
Revises: 002_authentication_system
Create Date: 2025-08-24 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_portfolio_schema_complete"
down_revision: Union[str, None] = "002_authentication_system"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add complete portfolio schema with all financial fields."""
    
    # Add missing financial columns to portfolios table
    op.add_column('portfolios', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('portfolios', sa.Column('initial_cash', sa.Numeric(15, 4), nullable=False, server_default='0.0000'))
    op.add_column('portfolios', sa.Column('current_cash', sa.Numeric(15, 4), nullable=False, server_default='0.0000'))
    op.add_column('portfolios', sa.Column('total_invested', sa.Numeric(15, 4), nullable=False, server_default='0.0000'))
    op.add_column('portfolios', sa.Column('daily_pnl', sa.Numeric(15, 4), nullable=False, server_default='0.0000'))
    op.add_column('portfolios', sa.Column('total_pnl', sa.Numeric(15, 4), nullable=False, server_default='0.0000'))
    op.add_column('portfolios', sa.Column('daily_return_pct', sa.Numeric(8, 4), nullable=False, server_default='0.0000'))
    op.add_column('portfolios', sa.Column('total_return_pct', sa.Numeric(8, 4), nullable=False, server_default='0.0000'))
    op.add_column('portfolios', sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('portfolios', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    
    # Update existing total_value precision to match model expectations
    op.alter_column('portfolios', 'total_value', 
                   type_=sa.Numeric(15, 4), 
                   nullable=False,
                   server_default='0.0000')
    
    # Add check constraint for base_currency 
    op.create_check_constraint(
        'ck_portfolios_base_currency',
        'portfolios', 
        "base_currency IN ('USD', 'EUR', 'GBP', 'CAD', 'JPY')"
    )
    
    # Create additional indexes for portfolio queries
    op.create_index('ix_portfolios_user_id', 'portfolios', ['user_id'])
    op.create_index('ix_portfolios_user_id_is_default', 'portfolios', ['user_id', 'is_default'])
    op.create_index('ix_portfolios_is_active', 'portfolios', ['is_active'])
    
    # Create positions table to support portfolio investments
    op.create_table(
        'positions',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('portfolio_id', sa.UUID(), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('quantity', sa.Numeric(15, 8), nullable=False),
        sa.Column('average_price', sa.Numeric(15, 4), nullable=False),
        sa.Column('market_price', sa.Numeric(15, 4), nullable=True),
        sa.Column('side', sa.String(10), nullable=False, server_default='long'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('portfolio_id', 'symbol', name='uix_portfolio_symbol')
    )
    
    # Create indexes for positions
    op.create_index('ix_positions_portfolio_id', 'positions', ['portfolio_id'])
    op.create_index('ix_positions_symbol', 'positions', ['symbol'])
    op.create_index('ix_positions_status', 'positions', ['status'])
    
    # Add check constraints for positions
    op.create_check_constraint('ck_positions_side', 'positions', "side IN ('long', 'short')")
    op.create_check_constraint('ck_positions_status', 'positions', "status IN ('active', 'closed', 'partial')")
    op.create_check_constraint('ck_positions_quantity_positive', 'positions', 'quantity > 0')


def downgrade() -> None:
    """Remove complete portfolio schema additions."""
    
    # Drop positions table
    op.drop_table('positions')
    
    # Drop portfolio indexes
    op.drop_index('ix_portfolios_is_active', 'portfolios')
    op.drop_index('ix_portfolios_user_id_is_default', 'portfolios') 
    op.drop_index('ix_portfolios_user_id', 'portfolios')
    
    # Drop check constraint
    op.drop_constraint('ck_portfolios_base_currency', 'portfolios', type_='check')
    
    # Revert total_value column to original type
    op.alter_column('portfolios', 'total_value', 
                   type_=sa.Numeric(20, 8),
                   nullable=True,
                   server_default='0.0')
    
    # Remove added columns
    op.drop_column('portfolios', 'is_active')
    op.drop_column('portfolios', 'is_default')
    op.drop_column('portfolios', 'total_return_pct')
    op.drop_column('portfolios', 'daily_return_pct')
    op.drop_column('portfolios', 'total_pnl')
    op.drop_column('portfolios', 'daily_pnl')
    op.drop_column('portfolios', 'total_invested')
    op.drop_column('portfolios', 'current_cash')
    op.drop_column('portfolios', 'initial_cash')
    op.drop_column('portfolios', 'description')
