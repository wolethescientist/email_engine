"""remove api_key_hash column

Revision ID: 0002_remove_api_key_hash
Revises: 0001_initial
Create Date: 2025-08-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_remove_api_key_hash'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop index if it exists to avoid errors on inconsistent DB states
    op.execute(sa.text('DROP INDEX IF EXISTS "ix_users_api_key_hash"'))

    # Drop column only if present
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c['name'] for c in inspector.get_columns('users')]
    if 'api_key_hash' in cols:
        with op.batch_alter_table('users') as batch_op:
            batch_op.drop_column('api_key_hash')


def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('api_key_hash', sa.String(length=128), nullable=True))
        batch_op.create_index('ix_users_api_key_hash', ['api_key_hash'], unique=False)