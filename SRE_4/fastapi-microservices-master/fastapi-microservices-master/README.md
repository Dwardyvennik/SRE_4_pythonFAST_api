# FastAPI Microservices Assignment

Containerized university project based on the original FastAPI microservices sample, refactored from the Pokemon/team domain into a simple shop and messaging system.

## Architecture

```text
fastapi-microservices-master/
├── auth-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/main.py
├── user-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/main.py
├── product-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/main.py
├── order-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/main.py
├── chat-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/main.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── nginx/
│   ├── default.conf
│   └── proxy_headers.conf
├── db-service/create.sql
└── docker-compose.yml
```

## Services

- `auth-service`: register, login, JWT creation, `/auth/me`
- `user-service`: authenticated user profile CRUD
- `product-service`: product CRUD with seeded demo products
- `order-service`: authenticated order creation; fetches product data over HTTP from `product-service`
- `chat-service`: authenticated user-to-user messages
- `nginx`: API gateway and static frontend host
- `postgres`: shared PostgreSQL database

## Run

```bash
docker compose up --build
```

Open:

- Frontend: `http://localhost:8080`
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

## Environment Variables

Each service reads configuration from environment variables in `docker-compose.yml`.

- `DATABASE_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `PRODUCT_SERVICE_URL` for `order-service`
