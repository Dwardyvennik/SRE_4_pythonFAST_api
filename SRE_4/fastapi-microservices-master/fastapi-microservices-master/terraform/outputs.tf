output "network_name" {
  description = "Docker network created by Terraform."
  value       = docker_network.assignment_network.name
}

output "postgres_volume_name" {
  description = "Docker volume created for PostgreSQL data."
  value       = docker_volume.postgres_data.name
}

output "grafana_volume_name" {
  description = "Docker volume created for Grafana data."
  value       = docker_volume.grafana_data.name
}

output "frontend_url" {
  description = "Frontend URL used by the Compose deployment."
  value       = "http://localhost:${var.http_port}"
}

output "prometheus_url" {
  description = "Prometheus URL used by the Compose deployment."
  value       = "http://localhost:${var.prometheus_port}"
}

output "grafana_url" {
  description = "Grafana URL used by the Compose deployment."
  value       = "http://localhost:${var.grafana_port}"
}
