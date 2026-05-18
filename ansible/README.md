# Ansible Automation — SRE End-Term Project

This directory contains the Ansible configuration management and deployment
automation for the **SRE End-Term Project**: a distributed microservices
e-commerce system with Docker Compose, Docker Swarm, Kubernetes, Prometheus,
and Grafana.

---

## Directory Structure

```
ansible/
├── ansible.cfg                     # Ansible global settings
├── inventory.ini                   # Target EC2 host
├── playbook.yml                    # Master playbook — runs all roles
├── group_vars/
│   └── all.yml                     # Shared variables (ports, paths, etc.)
└── roles/
    ├── docker/
    │   └── tasks/main.yml          # Install Docker Engine, Compose plugin, kubectl
    ├── deploy/
    │   └── tasks/main.yml          # Clone repo, validate Compose, build images
    ├── swarm/
    │   └── tasks/main.yml          # Init Docker Swarm, deploy docker-stack.yml
    ├── kubernetes/
    │   └── tasks/main.yml          # Validate/apply K8s manifests
    └── monitoring/
        └── tasks/main.yml          # Health-check Prometheus, Grafana, cAdvisor, UI
```

---

## Roles

### `docker`
Installs Docker CE, the Docker Compose plugin, and `kubectl` on the target host.

- Adds the official Docker apt repository
- Downloads a pinned kubectl client binary
- Adds the current user to the `docker` group
- Prints installed versions for evidence

### `deploy`
Clones the project repository, validates Docker Compose, and builds the images
that Swarm deploys.

- Clones/updates the repo to `/home/ubuntu/sre-microservices`
- Copies `.env.example` to `.env` on first run
- Validates Compose configuration
- Builds the Docker images with explicit names used by Swarm
- Stops any Compose containers so Swarm can own the published ports

### `swarm`
Initialises a single-node Docker Swarm cluster and deploys the stack using
`docker-stack.yml`.

- Checks if Swarm is already active (idempotent)
- Runs `docker swarm init` if needed
- Deploys or updates the stack via `docker stack deploy --resolve-image never`
- Prints service replica status

### `kubernetes`
Applies all Kubernetes manifests from the `k8s/` directory in dependency order.

- Validates manifests with `kubectl --dry-run=client` if no cluster is reachable
- Applies manifests only when a Kubernetes cluster is already available
- When a cluster exists, applies: namespace, configmap, postgres, services, nginx
- Waits for each deployment rollout to succeed
- Prints pod and service status

### `monitoring`
Verifies that every component of the observability stack is healthy.

- Polls Prometheus `/-/healthy` until it responds 200
- Polls Grafana `/login` until it responds 200
- Polls cAdvisor `/metrics` until it responds 200
- Polls the frontend until it responds 200
- Queries Prometheus for `up` metric and prints all scrape targets
- Prints a full access-URL summary at the end

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python 3 | ≥ 3.8 | `sudo apt install python3` |
| Ansible | ≥ 2.14 | `pip install ansible` |
| Docker | ≥ 24.0 | installed by the `docker` role |
| kubectl | any | installed by the `docker` role |
| Git | any | installed by the `docker` role |

---

## Quick Start (AWS EC2)

Terraform creates the EC2 instance. Ansible connects to it over SSH.

```bash
# 1. Install Ansible
pip install ansible

# 2. Put the Terraform EC2 public IP in inventory.ini

# 3. Enter the ansible directory
cd ansible

# 4. Run the full playbook
ansible-playbook playbook.yml
```

That's it. The playbook will install Docker and kubectl, clone the repo, build
images with Compose, deploy the live stack with Swarm, validate/apply K8s
manifests when possible, and verify monitoring.

---

## Run Individual Roles (using tags)

```bash
# Install Docker + kubectl only
ansible-playbook playbook.yml --tags docker

# Validate Compose and build images only
ansible-playbook playbook.yml --tags deploy

# Docker Swarm only
ansible-playbook playbook.yml --tags swarm

# Kubernetes manifests only
ansible-playbook playbook.yml --tags k8s

# Health-check monitoring stack only
ansible-playbook playbook.yml --tags monitoring
```

---

## Target The EC2 Server

Set `ansible/inventory.ini` after Terraform completes:

```ini
[sre_hosts]
sre-server ansible_host=YOUR_EC2_PUBLIC_IP ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/sre-key
```

Then run:

```bash
ansible-playbook playbook.yml
```

> If you use Terraform to provision the server, replace `YOUR_EC2_PUBLIC_IP` with:
> ```bash
> terraform output -raw instance_public_ip
> ```

---

## Variables

All shared variables live in `group_vars/all.yml`.
Key values:

| Variable | Default | Description |
|----------|---------|-------------|
| `app_dir` | `/home/ubuntu/sre-microservices` | Where the repo is cloned |
| `repo_url` | GitHub repo URL | Source repository |
| `frontend_port` | `8080` | Nginx / UI port |
| `prometheus_port` | `9091` | Prometheus port |
| `grafana_port` | `52057` | Grafana port |
| `cadvisor_port` | `8081` | cAdvisor port |
| `swarm_stack_name` | `sre-app` | Docker Swarm stack name |
| `k8s_namespace` | `microservices` | Kubernetes namespace |

---

## Access URLs (after playbook completes)

| Service | URL |
|---------|-----|
| Frontend (UI) | http://localhost:8080 |
| Auth API docs | http://localhost:8080/api/auth/docs |
| Product API docs | http://localhost:8080/api/products/docs |
| Order API docs | http://localhost:8080/api/orders/docs |
| Prometheus | http://localhost:9091 |
| Grafana | http://localhost:52057 (admin / admin) |
| cAdvisor | http://localhost:8081 |

---

## Relationship to Other Project Components

```
Terraform (terraform/)
    └─ Provisions Docker network + volumes
           │
           ▼
Ansible (ansible/)          ← YOU ARE HERE
    ├─ role: docker    → installs Docker Engine + kubectl
    ├─ role: deploy    → validates Compose and builds images
    ├─ role: swarm     → deploys Docker Swarm stack
    ├─ role: k8s       → validates/applies Kubernetes manifests
    └─ role: monitoring → verifies Prometheus + Grafana
```

Terraform creates the infrastructure (network, volumes). Ansible configures
the environment and deploys the application on top of it.

---

## Assignment Coverage

| Assignment | Requirement | Covered by |
|-----------|-------------|------------|
| Assignment 1 | Docker environment setup | `docker` role |
| Assignment 4 | Incident response automation | `sre-automation/` scripts |
| Assignment 5 | Infrastructure as Code | Terraform + this Ansible |
| Assignment 6 | Automated deployment | `deploy` + `swarm` roles |
| Assignment 6 | Health checks | `monitoring` role |
| End-Term | Multi-orchestration | `swarm` + `kubernetes` roles |
| End-Term | Configuration management | All roles |
