terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "assignment_network" {
  name = var.network_name
}

resource "docker_volume" "postgres_data" {
  name = var.postgres_volume_name
}

resource "docker_volume" "grafana_data" {
  name = var.grafana_volume_name
}
