# ServicePuls

A lightweight observability platform for monitoring the availability and performance of HTTP/HTTPS services.

ServicePuls continuously performs health checks against configured endpoints, collects response metrics, tracks incidents, and provides a centralized dashboard for monitoring service health and uptime.

The project is inspired by modern observability and uptime monitoring solutions such as Uptime Kuma, Grafana Synthetic Monitoring, and Datadog Synthetics.

---

## Features

### Service Monitoring

* HTTP/HTTPS endpoint monitoring
* Configurable monitoring intervals
* Response time measurements
* Availability tracking
* Automatic incident detection
* Incident history and recovery tracking

### Dashboard

* Real-time service status overview
* Uptime statistics
* Response time visualization
* Incident history
* Service-specific metrics

### Authentication & Security

* JWT-based authentication
* Protected API endpoints
* User-specific resources
* Password hashing and verification

### Observability

* Health-check endpoint
* Structured JSON logging
* Monitoring execution logs
* Error tracking

### Validation

* Request validation using Pydantic
* URL validation
* Input constraints
* Consistent API error responses

### Documentation

* OpenAPI specification
* Swagger UI
* ReDoc documentation

### Background Processing

* Celery workers
* Asynchronous monitoring jobs
* Scheduled health checks
* Incident processing in background tasks

---

## Architecture

```text
┌─────────────┐      REST API      ┌─────────────────┐
│ React + TS  │ ◄────────────────► │ FastAPI Backend │
└─────────────┘                    └────────┬────────┘
                                            │
                       ┌────────────────────┴──────────────────┐
                       │                                       │
                ┌──────▼───────┐                      ┌────────▼────────┐
                │ PostgreSQL   │                      │ Redis Broker    │
                │ Persistence  │                      │ Celery Backend  │
                └──────────────┘                      └────────┬────────┘
                                                               │
                                                               ▼
                                                       Celery Worker
                                                   Health Check Jobs
```

---

## Technology Stack

### Frontend

* React
* TypeScript
* Vite
* React Router
* Axios
* Recharts

### Backend

* FastAPI
* SQLAlchemy 2.x
* Alembic
* Pydantic
* JWT Authentication

### Database

* PostgreSQL

### Background Tasks

* Celery
* Redis

### Infrastructure

* Docker
* Docker Compose

### Observability

* Structlog
* OpenAPI
* Swagger UI
* ReDoc

---

## Core Domain

### User

Represents an authenticated platform user.

### Service

Represents a monitored HTTP/HTTPS endpoint.

**Example**

```json
{
  "name": "GitHub API",
  "url": "https://api.github.com",
  "check_interval": 60
}
```

### Check

Represents a single monitoring result.

**Stored information**

* HTTP status code
* Response time
* Timestamp
* Availability status

### Incident

Represents a service outage event.

Tracks:

* Incident start time
* Recovery time
* Total downtime duration

---

## Monitoring Workflow

1. User creates a monitored service.
2. Celery schedules periodic health checks.
3. Worker executes HTTP/HTTPS requests.
4. Response metrics are collected.
5. Results are persisted in PostgreSQL.
6. Service availability is evaluated.
7. Incidents are automatically created and resolved.
8. Dashboard displays current and historical metrics.

---

## API Documentation

FastAPI automatically generates OpenAPI documentation.

### Swagger UI

```text
http://localhost:8000/docs
```

### ReDoc

```text
http://localhost:8000/redoc
```

---

## Health Endpoint

Used for infrastructure and container health verification.

### Endpoint

```http
GET /health
```

### Example Response

```json
{
  "status": "ok",
  "database": "ok",
  "worker": "ok",
  "uptime_seconds": 12345
}
```

---

## Project Structure

```text
service-puls/
│
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── tasks/
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│   │
│   ├── package.json
│   └── Dockerfile
│
├── docs/
│   └── adr.md
│
├── docker-compose.yml
└── README.md
```

---

## Running the Project

### Clone Repository

```bash
git clone https://github.com/<your-username>/service-puls.git

cd service-puls
```

### Start Application

```bash
docker compose up --build
```

### DB migration
```bash
PYTHONPATH=backend alembic -c backend/alembic.ini revision --autogenerate -m "migration-name"
```

---

## Available Services

| Service     | URL                         |
| ----------- | --------------------------- |
| Frontend    | http://localhost:5173       |
| Backend API | http://localhost:8000       |
| Swagger UI  | http://localhost:8000/docs  |
| ReDoc       | http://localhost:8000/redoc |

---

## Academic Requirements

### Core Requirements

* REST API
* PostgreSQL Database
* React Frontend
* JWT Authentication
* Docker Compose Deployment
* Public GitHub Repository

### Additional Requirements

#### Observability

* Health endpoint
* Structured logging
* Monitoring logs

#### Data Validation

* Request validation
* URL validation
* Error handling

#### API Documentation

* OpenAPI specification
* Swagger UI
* ReDoc

#### Task Queue

* Celery workers
* Scheduled monitoring jobs
* Background task processing

---

## Future Improvements

* TCP monitoring
* SSL certificate expiration checks
* Email notifications
* Discord notifications
* Slack integration
* Prometheus metrics
* Grafana dashboards
* WebSocket live updates
* Multi-region monitoring
* Kubernetes deployment

---

## License

This project was developed for educational purposes as part of the Web Application Design course.
