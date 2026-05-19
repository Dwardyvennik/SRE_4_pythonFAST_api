from locust import HttpUser, between, task


class SREHealthUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(3)
    def products_health(self):
        self.client.get("/products/health", name="/products/health")

    @task(2)
    def orders_health(self):
        self.client.get("/orders/health", name="/orders/health")

    @task(2)
    def auth_health(self):
        self.client.get("/auth/health", name="/auth/health")

    @task(1)
    def users_health(self):
        self.client.get("/users/health", name="/users/health")

    @task(1)
    def notifications_health(self):
        self.client.get("/notifications/health", name="/notifications/health")

    @task(1)
    def chat_health(self):
        self.client.get("/chat/health", name="/chat/health")
