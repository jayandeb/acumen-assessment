# Portfolio Activity & Notification System

A mini microservices system built with FastAPI, Celery, and Redis that receives portfolio transaction events, persists them, and asynchronously delivers notifications based on user preferences and configurable rules.

---

## Architecture

```
                    ┌────────────────────────────────────────────────────────────┐
                    │                      Docker Network                         │
                    │                                                              │
  Client ────────▶ │  ┌──────────────┐     ┌───────────────────┐               │
  :8000             │  │  API Gateway  │────▶│ Portfolio Service  │               │
                    │  │    :8000      │     │      :8001         │               │
                    │  │              │     └────────┬──────────┘               │
                    │  │  JWT Auth    │              │ Celery send_task          │
                    │  │  Rate Limit  │     ┌────────▼──────────┐               │
                    │  │  Proxy       │     │       Redis         │               │
                    │  └──────────────┘     │      :6379         │               │
                    │         │             └────────┬──────────┘               │
                    │         │                      │ consume queue             │
                    │         │             ┌────────▼──────────┐               │
                    │         └────────────▶│ Notification Svc   │               │
                    │                       │      :8002         │               │
                    │                       │                    │               │
                    │                       │  Celery Worker     │               │
                    │                       │  (rule engine +    │               │
                    │                       │   mock channels)   │               │
                    │                       └───────────────────┘               │
                    │                                                              │
                    │  PostgreSQL :5432        Flower UI :5555                   │
                    └────────────────────────────────────────────────────────────┘
```

**Data flow:** Client sends request → API Gateway validates JWT and injects `X-User-ID` header → Portfolio Service persists transaction → publishes `process_notification_event` Celery task to Redis → Notification Worker evaluates rules against user preferences → dispatches to mock channels (EMAIL/SMS log, IN_APP saves to DB).

---

## Why FastAPI?

FastAPI's native async support and automatic OpenAPI documentation make it ideal for high-throughput microservices with minimal boilerplate. Its Pydantic integration enforces strict input validation at service boundaries, catching bad data before it reaches the database.

## Why Celery + Redis instead of direct HTTP?

Decoupling transaction creation from notification delivery via a message queue ensures that a slow or failed notification worker never blocks or degrades the portfolio write path. Celery's built-in retry mechanism with exponential back-off handles transient failures automatically, while Redis provides a lightweight broker that requires no additional infrastructure beyond what is already used for caching.

---

## How to Run Locally

### Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)

### 1. Clone and configure

```bash
git clone <repo-url>
cd portfolio-system
cp .env.example .env
# Edit .env if needed — defaults work out of the box
```

### 2. Start all services

```bash
docker compose up --build
```

Wait approximately 30–60 seconds for all services to become healthy on the first run.

### 3. Run the seed script

Run this once after the containers are up to create test users and preferences:

```bash
# From the project root (requires psycopg2-binary on host)
pip install psycopg2-binary sqlalchemy
DATABASE_URL=postgresql+asyncpg://portfolio:portfolio@localhost:5432/portfolio_db \
  python scripts/seed.py
```

Or run inside the notification container:

```bash
docker compose exec notification-service python /app/scripts/seed.py
```

### 4. Verify the system

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Login and capture the token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jayanta@test.com","password":"password123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Create a transaction (SELL triggers notification)
curl -s -X POST http://localhost:8000/portfolio/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"SELL","symbol":"AAPL","quantity":5,"price":180.00,"amount":900.00}' | python3 -m json.tool

# 4. List transactions
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/portfolio/transactions | python3 -m json.tool

# 5. Portfolio summary (cached after first call)
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/portfolio/summary | python3 -m json.tool

# 6. Check notifications
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/notifications | python3 -m json.tool
```

---

## Swagger Docs

Interactive API documentation: **http://localhost:8000/docs**

---

## Flower UI (Celery task monitor)

Real-time task queue and worker status: **http://localhost:5555**

---

## Test Users (after seeding)

| Email | Password | User ID |
|-------|----------|---------|
| jayanta@test.com | password123 | 00000000-0000-0000-0000-000000000001 |
| testuser@test.com | password123 | 00000000-0000-0000-0000-000000000002 |

---

## Notification Rules

| Transaction Type | Notification Triggered? |
|-----------------|------------------------|
| WITHDRAWAL | Always (all enabled channels) |
| SELL | Always (all enabled channels) |
| BUY | Only if `amount >= min_amount` preference |
| DEPOSIT | Never |

Default `min_amount` after seeding: **10,000** — small BUY orders will not trigger notifications.

---

## Tradeoffs

| Decision | Chosen | Alternative | Reason |
|----------|--------|-------------|--------|
| Message queue | Redis + Celery | Kafka / RabbitMQ | Lower ops overhead; sufficient for this scale |
| DB driver | asyncpg (async) + psycopg2 (Celery) | single driver | Celery is synchronous; FastAPI is async |
| Auth | Stateless JWT | Session store | Scales horizontally with no shared state |
| User store | In-memory in gateway | Separate user service | Avoids extra service for this scope |
| Migrations | Alembic | Manual SQL | Type-safe, version-controlled schema changes |
| Channels | Mock (log only) | SendGrid / Twilio | Out of scope; trivial to swap in real implementation |

---

## Scalability Notes

**API Gateway:** Stateless JWT validation means the gateway scales horizontally behind a load balancer with no shared state. Rate limiting state can be moved to Redis for multi-instance deployments using `slowapi`'s Redis storage backend.

**Portfolio Service:** The async SQLAlchemy engine supports connection pooling out of the box. Redis caching of portfolio summaries significantly reduces DB read load for high-frequency summary queries. The service scales horizontally; cache invalidation on write ensures consistency across replicas.

**Notification Service:** Celery workers are independently scalable — add more worker containers to increase notification throughput without touching the FastAPI layer. The `task_acks_late` and `task_reject_on_worker_lost` configuration ensures at-least-once delivery even during worker crashes, and the 3-retry exponential back-off handles transient downstream failures.
