"""add key_prefix to api_keys

Revision ID: c1a2b3d4e5f6
Revises: 487845ef1375
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'c1a2b3d4e5f6'
down_revision = '487845ef1375'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('api_keys', sa.Column('key_prefix', sa.String(16), nullable=True))
    op.create_index('ix_api_keys_key_prefix', 'api_keys', ['key_prefix'])
    # Remove the unique constraint on hashed_key (bcrypt hashes are non-deterministic)
    op.drop_index('ix_api_keys_hashed_key', table_name='api_keys')


def downgrade():
    op.create_index('ix_api_keys_hashed_key', 'api_keys', ['hashed_key'], unique=True)
    op.drop_index('ix_api_keys_key_prefix', table_name='api_keys')
    op.drop_column('api_keys', 'key_prefix')
