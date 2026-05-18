output "instance_public_ip" {
  description = "Public IP of the EC2 instance — paste this into ansible/inventory.ini"
  value       = aws_instance.sre_server.public_ip
}

output "instance_public_dns" {
  description = "Public DNS hostname of the EC2 instance"
  value       = aws_instance.sre_server.public_dns
}

output "ssh_command" {
  description = "Ready-to-use SSH command to connect to the server"
  value       = "ssh -i ${var.private_key_path} ubuntu@${aws_instance.sre_server.public_ip}"
}

output "frontend_url" {
  description = "URL for the app frontend after deployment"
  value       = "http://${aws_instance.sre_server.public_ip}:8080"
}

output "prometheus_url" {
  description = "URL for Prometheus after deployment"
  value       = "http://${aws_instance.sre_server.public_ip}:9091"
}

output "grafana_url" {
  description = "URL for Grafana after deployment"
  value       = "http://${aws_instance.sre_server.public_ip}:52057"
}

output "cadvisor_url" {
  description = "URL for cAdvisor after deployment"
  value       = "http://${aws_instance.sre_server.public_ip}:8081"
}
