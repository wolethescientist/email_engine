"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2025-08-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('encrypted_password', sa.String(), nullable=False),
        sa.Column('imap_host', sa.String(length=255), nullable=False),
        sa.Column('imap_port', sa.SmallInteger(), nullable=False),
        sa.Column('smtp_host', sa.String(length=255), nullable=False),
        sa.Column('smtp_port', sa.SmallInteger(), nullable=False),
        sa.Column('role', sa.Enum('admin', 'user', name='userrole'), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=False)

    op.create_table(
        'emails',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('folder', sa.String(length=32), nullable=False),
        sa.Column('subject', sa.String(length=998), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('from_address', sa.String(length=320), nullable=True),
        sa.Column('to_addresses', sa.Text(), nullable=True),
        sa.Column('cc_addresses', sa.Text(), nullable=True),
        sa.Column('bcc_addresses', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_emails_user_id', 'emails', ['user_id'], unique=False)
    op.create_index('ix_emails_folder', 'emails', ['folder'], unique=False)
    op.create_index('ix_emails_is_read', 'emails', ['is_read'], unique=False)

    op.create_table(
        'attachments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=512), nullable=False),
        sa.Column('content_type', sa.String(length=128), nullable=True),
        sa.Column('blob', sa.LargeBinary(), nullable=True),
        sa.ForeignKeyConstraint(['email_id'], ['emails.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_attachments_email_id', 'attachments', ['email_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_attachments_email_id', table_name='attachments')
    op.drop_table('attachments')

    op.drop_index('ix_emails_is_read', table_name='emails')
    op.drop_index('ix_emails_folder', table_name='emails')
    op.drop_index('ix_emails_user_id', table_name='emails')
    op.drop_table('emails')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')