# ServicePulse

> Lightweight uptime monitoring platform — self-hosted, fully containerized, **Uptime Kuma**-inspired.

ServicePulse continuously pings configured HTTP/HTTPS endpoints, measures response times, detects outages automatically, and presents everything on a real-time dashboard. Built as a full-stack web application with a task-queue architecture using Dramatiq + Redis.

---

## Features

| Category | Details |
|---|---|
| **Monitoring** | HTTP/HTTPS health checks, configurable interval (10 s – 86 400 s), response time tracking |
| **Incident management** | Automatic incident creation on failure, automatic resolution on recovery, full incident history |
| **Dashboard** | Real-time service status overview, uptime percentage, response time charts (Recharts) |
| **Authentication** | JWT-based auth, bcrypt password hashing, per-user resource isolation |
| **Background tasks** | Dramatiq workers, APScheduler for per-service job scheduling, worker heartbeat monitoring |
| **Observability** | Structured JSON logging (structlog), `/health` endpoint with component-level status |
| **API docs** | Auto-generated OpenAPI spec, Swagger UI, ReDoc |

---

## Architecture

```
┌─────────────────────┐          REST API          ┌────────────────────────┐
│   React + TypeScript │ ◄─────────────────────────► │    FastAPI Backend      │
│   Vite · Recharts    │                              │  SQLAlchemy · Pydantic  │
└─────────────────────┘                              └───────────┬────────────┘
                                                                 │
                                          ┌──────────────────────┴──────────────────────┐
                                          │                                             │
                                 ┌────────▼────────┐                          ┌─────────▼────────┐
                                 │   PostgreSQL 17  │                          │    Redis 8.8     │
                                 │   (persistence)  │                          │  (task broker)   │
                                 └─────────────────┘                          └─────────┬────────┘
                                                                                        │
                                                                               ┌────────▼────────┐
                                                                               │  Dramatiq Worker │
                                                                               │  Health Checks   │
                                                                               └─────────────────┘
```

**Monitoring flow:**
1. User registers a service (URL + check interval)
2. APScheduler schedules a periodic job for that service
3. On each tick, the job pushes a `ping_service_task` message to Redis
4. Dramatiq worker picks up the message, sends an HTTP request, records the result
5. If the response indicates failure → incident is opened; on recovery → incident is closed
6. Frontend polls the API and renders current status, uptime %, and response time history

---

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — async REST API framework
- [SQLAlchemy 2.x](https://docs.sqlalchemy.org/) — ORM with mapped column syntax
- [Alembic](https://alembic.sqlalchemy.org/) — database migrations
- [Pydantic v2](https://docs.pydantic.dev/) — request/response validation
- [Dramatiq](https://dramatiq.io/) + [Redis](https://redis.io/) — task queue
- [APScheduler](https://apscheduler.readthedocs.io/) — per-service interval scheduling
- [httpx](https://www.python-httpx.org/) — async-capable HTTP client for health checks
- [structlog](https://www.structlog.org/) — structured JSON logging
- [bcrypt](https://pypi.org/project/bcrypt/) + [PyJWT](https://pyjwt.readthedocs.io/) — auth

**Frontend**
- [React 19](https://react.dev/) + [TypeScript 6](https://www.typescriptlang.org/)
- [Vite 8](https://vitejs.dev/) — build tooling
- [React Router v7](https://reactrouter.com/)
- [Recharts](https://recharts.org/) — response time visualization

**Infrastructure**
- Docker + Docker Compose (5 services)
- GitHub Actions CI/CD → Azure Container Registry (ACR)
- PostgreSQL 17 · Redis 8.8

---

## Project Structure

```
ServicePulse/
├── backend/
│   ├── database/
│   │   ├── core/            # SQLAlchemy engine & session
│   │   ├── User.py          # User model
│   │   ├── Service.py       # Service model
│   │   ├── Check.py         # Check model (single ping result)
│   │   └── Incident.py      # Incident model (outage tracking)
│   ├── routes/
│   │   ├── auth.py          # POST /auth/register, /auth/login
│   │   └── services.py      # CRUD /services + checks + incidents
│   ├── tasks/
│   │   ├── monitor_tasks.py # Dramatiq actors: ping_service_task, heartbeat
│   │   └── scheduler.py     # APScheduler init & job management
│   ├── utils/
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── security/        # JWT, bcrypt helpers
│   │   └── logger/          # structlog setup
│   ├── alembic/             # DB migration scripts
│   ├── main.py              # App entrypoint, /health endpoint
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── api/             # Typed fetch client
│       ├── components/      # StatusBadge, ServiceModal, ChartTooltip, Layout
│       ├── hooks/           # useAuth
│       ├── pages/           # AuthPage, DashboardPage, ServiceDetailPage
│       ├── router/          # React Router config
│       └── types/           # Shared TS interfaces
├── .github/
│   └── workflows/
│       └── build.yml        # CI/CD → Azure ACR
├── docker-compose.yml
└── .env                     # (see configuration below)
```

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/ServicePulse.git
cd ServicePulse
```

### 2. Configure environment variables

Copy the template and fill in the required values:

```bash
cp .env_backbone .env
```

```env
# PostgreSQL
POSTGRES_USER=servicepulse
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=servicepulse_db
DB_HOST=postgres-db
DB_PORT=5432

# Redis / Dramatiq
REDIS_URL=redis://redis-worker:6379/0

# JWT
JWT_SECRET_KEY=your_secret_key_here

# Frontend (baked in at build time)
VITE_API_URL=http://localhost:13000

TZ=Europe/Warsaw
```

### 3. Start the application

```bash
docker compose up --build
```

This starts 5 containers: `postgres-db`, `redis-worker`, `monitoring_worker`, `service-backend`, `frontend-service`.

### 4. Run database migrations

```bash
docker compose exec service-backend alembic -c /backend/alembic.ini upgrade head
```

---

## Available Services

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:13000 |
| Swagger UI | http://localhost:13000/docs |
| ReDoc | http://localhost:13000/redoc |
| Health check | http://localhost:13000/health |

---

## API Reference

### Authentication

```http
POST /auth/register      # Create account
POST /auth/login         # Get JWT token (OAuth2 password flow)
```

### Services

```http
GET    /services/               # List all services for current user
POST   /services/               # Register a new monitored service
GET    /services/{id}           # Get service details
PUT    /services/{id}           # Update service (name / URL / interval)
DELETE /services/{id}           # Delete service and cancel its scheduler job
```

### Checks & Incidents

```http
GET /services/{id}/checks       # Paginated check history (default: last 50)
GET /services/{id}/incidents    # Full incident history for a service
GET /services/incidents/active  # All currently open incidents
```

### Health

```http
GET /health
```

```json
{
  "status": "ok",
  "components": {
    "database": "ok",
    "redis": "ok",
    "worker": "ok"
  }
}
```

The endpoint returns `200` when all components are healthy, `503` otherwise. Worker health is determined by a Redis heartbeat updated every 60 seconds by a dedicated Dramatiq actor.

---

## CI/CD

On every push to `main`, GitHub Actions builds and pushes Docker images to **Azure Container Registry**:

```
nexoregistryheczko.azurecr.io/sp-backend-prod:latest
nexoregistryheczko.azurecr.io/sp-frontend-prod:latest
```

Required repository secrets: `ACR_USERNAME`, `ACR_PASSWORD`, `VITE_API_URL`.

---

## Database Migrations

Generate a new migration after model changes:

```bash
PYTHONPATH=backend alembic -c backend/alembic.ini revision --autogenerate -m "migration-name"
```

Apply pending migrations:

```bash
PYTHONPATH=backend alembic -c backend/alembic.ini upgrade head
```

---

## Roadmap

- [ ] WebSocket live updates (no more polling)
- [ ] Email / Discord / Slack notifications on incident open/close
- [ ] TCP port monitoring
- [ ] SSL certificate expiration checks
- [ ] Prometheus metrics endpoint + Grafana dashboard
- [ ] Multi-user teams & shared service groups
- [ ] Kubernetes deployment manifests

---

## License

Developed for educational purposes as part of the **Projektowanie Aplikacji Internetowych** course at Jagiellonian University (UJ WFAIS).