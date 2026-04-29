# FastAPI Microservices Assignment

Containerized university project based on the original FastAPI microservices sample, refactored from the Pokemon/team domain into a simple shop and messaging system with monitoring.

## Architecture

```text
fastapi-microservices-master/
|-- auth-service/
|   |-- .dockerignore
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- app/main.py
|-- user-service/
|   |-- .dockerignore
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- app/main.py
|-- product-service/
|   |-- .dockerignore
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- app/main.py
|-- order-service/
|   |-- .dockerignore
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- app/main.py
|-- chat-service/
|   |-- .dockerignore
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- app/main.py
|-- frontend/
|   |-- index.html
|   |-- styles.css
|   `-- app.js
|-- nginx/
|   |-- default.conf
|   `-- proxy_headers.conf
|-- prometheus/
|   `-- prometheus.yml
|-- db-service/create.sql
`-- docker-compose.yml
```

## Services

- `auth-service`: register, login, JWT creation, `/auth/me`, `/metrics`
- `user-service`: authenticated user profile CRUD, `/metrics`
- `product-service`: product CRUD with seeded demo products, `/metrics`
- `order-service`: authenticated order creation; fetches product data over HTTP from `product-service`, `/metrics`
- `chat-service`: authenticated user-to-user messages, `/metrics`
- `nginx`: API gateway and static frontend host
- `postgres`: shared PostgreSQL database
- `prometheus`: scrapes service metrics over the Docker network
- `grafana`: visualizes Prometheus metrics

## Run

```bash
docker compose up --build
```

Open:

- Frontend: `http://localhost:8080`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` with username `admin` and password `admin`
- Auth docs: `http://localhost:8080/api/auth/docs`
- User docs: `http://localhost:8080/api/users/docs`
- Product docs: `http://localhost:8080/api/products/docs`
- Order docs: `http://localhost:8080/api/orders/docs`
- Chat docs: `http://localhost:8080/api/chat/docs`

## API Gateway Routes

- `/api/auth/*` -> `auth-service`
- `/api/users/*` -> `user-service`
- `/api/products/*` -> `product-service`
- `/api/orders/*` -> `order-service`
- `/api/chat/*` -> `chat-service`

## Monitoring

Every FastAPI service uses `prometheus-fastapi-instrumentator` and exposes metrics at `/metrics`.

Code snippet added to every `app/main.py`:

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(...)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

Prometheus scrape targets are defined in `prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: auth-service
    metrics_path: /metrics
    static_configs:
      - targets: ["auth-service:8000"]
  - job_name: user-service
    metrics_path: /metrics
    static_configs:
      - targets: ["user-service:8000"]
  - job_name: product-service
    metrics_path: /metrics
    static_configs:
      - targets: ["product-service:8000"]
  - job_name: order-service
    metrics_path: /metrics
    static_configs:
      - targets: ["order-service:8000"]
  - job_name: chat-service
    metrics_path: /metrics
    static_configs:
      - targets: ["chat-service:8000"]
```

## Grafana Dashboard

1. Open `http://localhost:3000`.
2. Login with `admin` / `admin`.
3. Add Prometheus data source with URL `http://prometheus:9090`.
4. Create a dashboard and add panels with these PromQL queries.

Service Availability:

```promql
up
```

Request Rate:

```promql
sum(rate(http_requests_total[1m])) by (job)
```

5xx Error Rate:

```promql
sum(rate(http_requests_total{status=~"5.."}[1m])) by (job)
```

Average Latency:

```promql
rate(http_request_duration_seconds_sum[1m])
/
rate(http_request_duration_seconds_count[1m])
```

p95 Latency:

```promql
histogram_quantile(
  0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, job)
)
```

Memory Usage:

```promql
process_resident_memory_bytes
```

CPU Usage:

```promql
rate(process_cpu_seconds_total[1m])
```

## Order-Service Incident Simulation

Start the stack:

```bash
docker compose up -d --build
```

Create a test user and save the JWT:

```bash
curl -s -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"incident_user\",\"email\":\"incident@example.com\",\"password\":\"password123\"}"
```

Break `order-service` by overriding the database hostname:

```bash
docker compose -f docker-compose.yml -f docker-compose.incident.yml up -d --force-recreate order-service
```

Generate traffic and check Prometheus:

```bash
curl "http://localhost:9090/api/v1/query?query=up%7Bjob%3D%22order-service%22%7D"
```

Check Prometheus targets:

```text
http://localhost:9090/targets
```

Expected result:

- `order-service` shows `DOWN` or failed scrapes while the bad database hostname prevents startup.
- Grafana `Service Availability` panel shows `up{job="order-service"} = 0`.
- If the app starts but database calls fail, request panels show 5xx growth for `order-service`.

Fix and restart:

```bash
docker compose up -d --force-recreate order-service
```

Verify recovery:

```bash
docker compose ps order-service
curl http://localhost:9090/api/v1/query?query=up%7Bjob%3D%22order-service%22%7D
```

Expected recovery:

- `order-service` returns to `UP` in Prometheus targets.
- Grafana `Service Availability` returns to `1` for `order-service`.
- Request rate resumes normally after new traffic.

## Environment Variables

Each service reads configuration from environment variables in `docker-compose.yml`.

- `DATABASE_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `PRODUCT_SERVICE_URL` for `order-service`
