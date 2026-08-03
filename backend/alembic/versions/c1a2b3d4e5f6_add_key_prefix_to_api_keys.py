"""add key_prefix to api_keys

Revision ID: c1a2b3d4e5f6
Revises: 487845ef1375
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

revision = 'c1a2b3d4e5f6'
down_revision = '487845ef1375'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('api_keys', sa.Column('key_prefix', sa.String(16), nullable=True))

    connection = op.get_bind()
    keys = connection.execute(sa.text("SELECT id, hashed_key FROM api_keys")).fetchall()
    for key_id, raw_key in keys:
        if not raw_key.startswith('$2b$'):
            connection.execute(
                sa.text("UPDATE api_keys SET key_prefix = :prefix, hashed_key = :hashed WHERE id = :id"),
                {"prefix": raw_key[:16], "hashed": pwd_context.hash(raw_key), "id": key_id}
            )

    op.create_index('ix_api_keys_key_prefix', 'api_keys', ['key_prefix'])
    op.drop_index('ix_api_keys_hashed_key', table_name='api_keys')


def downgrade():
    op.create_index('ix_api_keys_hashed_key', 'api_keys', ['hashed_key'], unique=True)
    op.drop_index('ix_api_keys_key_prefix', table_name='api_keys')
    op.drop_column('api_keys', 'key_prefix')
