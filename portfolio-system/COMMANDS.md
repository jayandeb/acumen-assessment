# Commands Reference

## Start the System

```bash
# 1. Go to the project folder
cd "portfolio-system"

# 2. Copy environment file (first time only)
cp .env.example .env

# 3. Build and start all services
docker compose up --build

# Start in background (detached)
docker compose up --build -d

# Stop everything
docker compose down

# Stop and wipe the database volume
docker compose down -v
```

---

## Seed the Database

Run this after `docker compose up` to create test users and notification preferences.

```bash
# From inside the project folder:
docker compose exec notification-service python scripts/seed.py
```

Expected output:
```
Test users created:
  jayanta@test.com / password123  (user_id: 00000000-0000-0000-0000-000000000001)
  testuser@test.com / password123  (user_id: 00000000-0000-0000-0000-000000000002)

Notification preferences seeded (all channels enabled, min_amount=10000)
```

---

## Test the API

### 1. Health check
```bash
curl http://localhost:8000/health
```

### 2. Login and get token
```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jayanta@test.com","password":"password123"}' | jq
```

Copy the `access_token` from the response, then set it:
```bash
TOKEN="paste_your_access_token_here"
```

### 3. Create a transaction
```bash
# BUY (amount below 10000 — will NOT trigger notification)
curl -s -X POST http://localhost:8000/portfolio/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"BUY","symbol":"AAPL","quantity":10,"price":175.50,"amount":1755.00}' | jq

# BUY (amount above 10000 — WILL trigger notification)
curl -s -X POST http://localhost:8000/portfolio/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"BUY","symbol":"TSLA","quantity":50,"price":250.00,"amount":12500.00}' | jq

# SELL (always triggers notification)
curl -s -X POST http://localhost:8000/portfolio/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"SELL","symbol":"AAPL","quantity":5,"price":180.00,"amount":900.00}' | jq

# WITHDRAWAL (always triggers notification)
curl -s -X POST http://localhost:8000/portfolio/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"WITHDRAWAL","amount":500.00}' | jq

# With idempotency key (safe to retry — returns same result)
curl -s -X POST http://localhost:8000/portfolio/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"DEPOSIT","amount":5000.00,"idempotency_key":"unique-key-123"}' | jq
```

### 4. List transactions (paginated)
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/portfolio/transactions" | jq

# With pagination
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/portfolio/transactions?limit=5&offset=0" | jq
```

### 5. Portfolio summary (cached after first call)
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/portfolio/summary | jq
```

### 6. View notifications
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/notifications | jq
```

### 7. View notification preferences
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/preferences | jq
```

### 8. Update a preference
```bash
# Lower min_amount for BUY notifications to $100
curl -s -X PUT http://localhost:8000/preferences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"channel":"IN_APP","enabled":true,"min_amount":100}' | jq

# Disable SMS notifications
curl -s -X PUT http://localhost:8000/preferences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"channel":"SMS","enabled":false,"min_amount":0}' | jq
```

### 9. Refresh token
```bash
curl -s -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"paste_refresh_token_here"}' | jq
```

---

## UIs

| UI | URL | What it shows |
|----|-----|---------------|
| Swagger / API docs | http://localhost:8000/docs | Interactive API explorer |
| ReDoc | http://localhost:8000/redoc | Readable API reference |
| Flower (Celery) | http://localhost:5555 | Task queue, worker status, task history |

---

## Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api-gateway
docker compose logs -f portfolio-service
docker compose logs -f notification-service
docker compose logs -f notification-worker
```

---

## Useful Docker Commands

```bash
# Check which containers are running
docker compose ps

# Restart a single service (e.g. after code change)
docker compose restart portfolio-service

# Rebuild a single service
docker compose up --build portfolio-service

# Open a shell inside a container
docker compose exec portfolio-service bash
docker compose exec notification-service bash

# Run Alembic migrations manually
docker compose exec portfolio-service alembic upgrade head
docker compose exec notification-service alembic upgrade head
```

---

## Test Users

| Email | Password | User ID |
|-------|----------|---------|
| jayanta@test.com | password123 | 00000000-0000-0000-0000-000000000001 |
| testuser@test.com | password123 | 00000000-0000-0000-0000-000000000002 |

---

## Notification Rules (quick reference)

| Transaction Type | Notification sent? |
|-----------------|-------------------|
| WITHDRAWAL | Always |
| SELL | Always |
| BUY | Only if `amount >= min_amount` (default: 10,000) |
| DEPOSIT | Never |
