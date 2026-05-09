from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum('BUY', 'SELL', 'DEPOSIT', 'WITHDRAWAL', name='transactiontype'), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=True),
        sa.Column('quantity', sa.Numeric(18, 8), nullable=True),
        sa.Column('price', sa.Numeric(18, 8), nullable=True),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column(
            'status',
            sa.Enum('PENDING', 'COMPLETED', 'FAILED', name='transactionstatus'),
            server_default='COMPLETED',
        ),
        sa.Column('idempotency_key', sa.String(255), unique=True, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_transactions_user_id', 'transactions')
    op.drop_table('transactions')
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS transactionstatus")
