"""Add nullable, versioned forensic context snapshot without altering history."""
from alembic import op
import sqlalchemy as sa

revision = 'a61000000005'
down_revision = '146af5c0448f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('analyses', sa.Column('context_snapshot', sa.JSON(), nullable=True))


def downgrade():
    raise RuntimeError('Snapshot removal would discard forensic records; explicit archival migration required')
