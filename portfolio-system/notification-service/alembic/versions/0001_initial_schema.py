from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'channel',
            sa.Enum('EMAIL', 'SMS', 'IN_APP', name='notificationchannel'),
            nullable=False,
        ),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column(
            'status',
            sa.Enum('SENT', 'FAILED', name='notificationstatus'),
            server_default='SENT',
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])

    op.create_table(
        'notification_preferences',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'channel',
            sa.Enum('EMAIL', 'SMS', 'IN_APP', name='notificationchannel'),
            nullable=False,
        ),
        sa.Column('enabled', sa.Boolean, server_default='true'),
        sa.Column('min_amount', sa.Numeric(18, 2), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index(
        'ix_notification_preferences_user_id',
        'notification_preferences',
        ['user_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_notification_preferences_user_id', 'notification_preferences')
    op.drop_table('notification_preferences')
    op.drop_index('ix_notifications_user_id', 'notifications')
    op.drop_table('notifications')
    op.execute("DROP TYPE IF EXISTS notificationchannel")
    op.execute("DROP TYPE IF EXISTS notificationstatus")
