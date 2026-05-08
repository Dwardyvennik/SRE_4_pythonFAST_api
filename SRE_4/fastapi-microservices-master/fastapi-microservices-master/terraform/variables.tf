variable "network_name" {
  description = "Docker network reserved for Assignment 6 infrastructure evidence."
  type        = string
  default     = "assignment6_microservices_net"
}

variable "postgres_volume_name" {
  description = "Docker volume reserved for PostgreSQL data."
  type        = string
  default     = "assignment6_postgres_data"
}

variable "grafana_volume_name" {
  description = "Docker volume reserved for Grafana data."
  type        = string
  default     = "assignment6_grafana_data"
}

variable "http_port" {
  description = "Frontend/reverse proxy port used by docker-compose.yml."
  type        = number
  default     = 8080
}

variable "prometheus_port" {
  description = "Prometheus host port used by docker-compose.yml."
  type        = number
  default     = 9091
}

variable "grafana_port" {
  description = "Grafana host port used by docker-compose.yml."
  type        = number
  default     = 52057
}
