import os
import sys
import uuid

from sqlalchemy import create_engine, text

TEST_USERS = [
    {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "email": "jayanta@test.com",
        "password": "password123",
    },
    {
        "user_id": "00000000-0000-0000-0000-000000000002",
        "email": "testuser@test.com",
        "password": "password123",
    },
]

CHANNELS = ["EMAIL", "SMS", "IN_APP"]
MIN_AMOUNT = 10000


def main() -> None:
    raw_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://portfolio:portfolio@localhost:5432/portfolio_db",
    )
    sync_url = raw_url.replace("+asyncpg", "+psycopg2")

    try:
        import psycopg2
    except ImportError:
        print("psycopg2 not installed. Install it with: pip install psycopg2-binary")
        sys.exit(1)

    engine = create_engine(sync_url, echo=False)

    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
        conn.execute(
            text("""
                DO $$ BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationchannel') THEN
                        CREATE TYPE notificationchannel AS ENUM ('EMAIL', 'SMS', 'IN_APP');
                    END IF;
                END $$;
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    channel notificationchannel NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    min_amount NUMERIC(18,2) DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ DEFAULT now()
                )
            """)
        )
        conn.commit()

        for user in TEST_USERS:
            for channel in CHANNELS:
                existing = conn.execute(
                    text(
                        "SELECT id FROM notification_preferences "
                        "WHERE user_id = :uid AND channel = :ch"
                    ),
                    {"uid": user["user_id"], "ch": channel},
                ).fetchone()
                if not existing:
                    conn.execute(
                        text("""
                            INSERT INTO notification_preferences
                                (id, user_id, channel, enabled, min_amount)
                            VALUES
                                (:id, :user_id, :channel, true, :min_amount)
                        """),
                        {
                            "id": str(uuid.uuid4()),
                            "user_id": user["user_id"],
                            "channel": channel,
                            "min_amount": MIN_AMOUNT,
                        },
                    )
        conn.commit()

    print("Test users created:")
    for user in TEST_USERS:
        print(f"  {user['email']} / {user['password']}  (user_id: {user['user_id']})")
    print("\nNotification preferences seeded (all channels enabled, min_amount=10000)")


if __name__ == "__main__":
    main()
