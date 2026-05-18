# Terraform Infrastructure Evidence

This directory provides minimal Terraform evidence for Assignment 6.

The application itself is deployed with `docker compose` from the repository root. These Terraform files provision simple Docker infrastructure resources that match the Compose deployment concept:

- a Docker network
- a PostgreSQL data volume
- a Grafana data volume
- outputs for the frontend, Prometheus, and Grafana URLs

## Commands

```bash
cd terraform
terraform init
terraform fmt
terraform validate
terraform plan
```

Applying this Terraform configuration is optional for the assignment evidence. It creates separate Docker resources prefixed with `assignment6_` and does not replace the main `docker-compose.yml` deployment.
