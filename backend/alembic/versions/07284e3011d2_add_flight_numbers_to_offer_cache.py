"""add_flight_numbers_to_offer_cache

Revision ID: 07284e3011d2
Revises: f9d8f6e0b502
Create Date: 2026-02-10 15:06:14.077347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07284e3011d2'
down_revision: Union[str, None] = 'f9d8f6e0b502'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add flight_numbers column to flight_offer_cache
    op.add_column(
        'flight_offer_cache',
        sa.Column('flight_numbers', sa.dialects.postgresql.JSONB, nullable=True)
    )
    
    # Create index for faster flight number lookup
    op.execute("""
        CREATE INDEX ix_flight_offer_cache_flight_numbers 
        ON flight_offer_cache USING GIN (flight_numbers)
    """)


def downgrade() -> None:
    # Drop index first
    op.drop_index('ix_flight_offer_cache_flight_numbers', table_name='flight_offer_cache')
    
    # Drop column
    op.drop_column('flight_offer_cache', 'flight_numbers')
