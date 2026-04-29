variable "project_name" {
  description = "Project name used for infrastructure resource naming."
  type        = string
  default     = "microservices-assignment"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}
