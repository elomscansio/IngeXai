"""Initial schema

Revision ID: 20240610_01
Revises: 
Create Date: 2024-06-10

"""
from alembic import op
import sqlalchemy as sa

revision = '20240610_01'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String, unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False)
    )
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('owner_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False)
    )
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('document_id', sa.Integer, sa.ForeignKey('documents.id'), nullable=False, index=True),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('chunk_text', sa.Text, nullable=False),
        sa.Column('embedding', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('status', sa.String, default="active")
    )

def downgrade():
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('users')
