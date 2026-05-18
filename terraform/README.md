# AWS Deployment Guide — SRE End-Term Project

This guide walks you through deploying the full SRE microservices stack
to AWS using **Terraform** (infrastructure) and **Ansible** (configuration).

---

## What Gets Created on AWS

```
AWS (us-east-1)
└── EC2 t2.micro  (free tier, Ubuntu 22.04)
    ├── Security Group — opens ports 22, 8080, 9091, 52057, 8081
    └── 20 GB EBS volume (gp2)
```

After Ansible runs, the EC2 will have:
- Docker Engine + Compose plugin
- kubectl
- Your microservices stack (Compose-built images, Swarm runtime, K8s manifests)
- Prometheus, Grafana, cAdvisor

---

## Prerequisites (install once)

```bash
# Terraform
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt-get update && sudo apt-get install terraform

# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Ansible
sudo apt-get install -y python3-pip
pip3 install ansible

# Verify
terraform version
aws --version
ansible --version
```

---

## Step 1 — Configure AWS credentials

```bash
aws configure
```

You will be prompted for:

```
AWS Access Key ID:     <your key>
AWS Secret Access Key: <your secret>
Default region name:   us-east-1
Default output format: json
```

**Where to get your keys:**
1. Log in to AWS Console → top-right menu → **Security credentials**
2. Scroll to **Access keys** → **Create access key**
3. Download the CSV — you will not see the secret again

---

## Step 2 — Generate SSH key pair

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/sre-key -N ""
```

This creates:
- `~/.ssh/sre-key`      ← private key (never share this)
- `~/.ssh/sre-key.pub`  ← public key (Terraform uploads this to AWS)

---

## Step 3 — Provision infrastructure with Terraform

```bash
cd terraform/

# Download the AWS provider
terraform init

# Preview what will be created. Replace the CIDR with your own public IP when possible.
terraform plan -var "allowed_admin_cidr=YOUR_PUBLIC_IP/32"

# Create the EC2 instance (takes ~1 minute)
terraform apply -var "allowed_admin_cidr=YOUR_PUBLIC_IP/32"
# Type: yes
```

At the end you will see output like:

```
instance_public_ip = "54.123.45.67"
ssh_command        = "ssh -i ~/.ssh/sre-key ubuntu@54.123.45.67"
frontend_url       = "http://54.123.45.67:8080"
prometheus_url     = "http://54.123.45.67:9091"
grafana_url        = "http://54.123.45.67:52057"
```

**Save the public IP** — you need it for the next step.

---

## Step 4 — Update Ansible inventory

Open `ansible/inventory.ini` and replace `YOUR_EC2_PUBLIC_IP`:

```ini
sre-server ansible_host=54.123.45.67 \    ← paste your IP here
```

Or do it with a one-liner:

```bash
# Get IP automatically from Terraform output
export EC2_IP=$(terraform -chdir=terraform output -raw instance_public_ip)

# Inject into inventory
sed -i "s/YOUR_EC2_PUBLIC_IP/$EC2_IP/" ansible/inventory.ini
```

---

## Step 5 — Wait for EC2 to be ready (~60 seconds)

EC2 needs a minute to boot and run its user_data script (installs Python3).
Test SSH access:

```bash
ssh -i ~/.ssh/sre-key ubuntu@YOUR_EC2_IP
# Should log you in — type exit to leave
```

---

## Step 6 — Run Ansible playbook

```bash
cd ansible/

# Full deployment (all roles)
ansible-playbook playbook.yml
```

This will:
1. **docker role** — install Docker CE + Compose + kubectl (~3 min)
2. **deploy role** — clone repo, validate Compose, build Docker images (~5 min)
3. **swarm role** — init Swarm, deploy docker-stack.yml as the live runtime (~1 min)
4. **kubernetes role** — validate manifests; apply them if a cluster exists (~1 min)
5. **monitoring role** — health-check everything, print URLs (~1 min)

Total: ~12 minutes on t2.micro.

---

## Step 7 — Access your deployed stack

Replace `EC2_IP` with your actual IP from Step 3:

| Service | URL |
|---------|-----|
| Frontend (UI) | `http://EC2_IP:8080` |
| Auth API docs | `http://EC2_IP:8080/api/auth/docs` |
| Product API docs | `http://EC2_IP:8080/api/products/docs` |
| Order API docs | `http://EC2_IP:8080/api/orders/docs` |
| Prometheus | `http://EC2_IP:9091` |
| Grafana | `http://EC2_IP:52057` — login: `admin` / `admin` |
| cAdvisor | `http://EC2_IP:8081` |

---

## Run Individual Roles

```bash
# Install Docker only
ansible-playbook playbook.yml --tags docker

# Validate Compose and build images only
ansible-playbook playbook.yml --tags deploy

# Docker Swarm only
ansible-playbook playbook.yml --tags swarm

# Kubernetes only
ansible-playbook playbook.yml --tags k8s

# Verify monitoring only
ansible-playbook playbook.yml --tags monitoring
```

---

## Incident Simulation (on EC2)

SSH into the server:

```bash
ssh -i ~/.ssh/sre-key ubuntu@YOUR_EC2_IP
cd ~/sre-microservices/SRE_4_pythonFAST_api
```

Break the order-service (wrong DB host):

```bash
docker compose -f docker-compose.yml \
  -e ORDER_DATABASE_URL=postgresql+psycopg2://postgres:postgres@wrong-host:5432/microservices_db \
  up -d --force-recreate order-service
```

Watch it fail in Prometheus:

```bash
curl "http://localhost:9091/api/v1/query?query=up{job=\"order-service\"}"
```

Fix it:

```bash
docker compose up -d --force-recreate order-service
```

---

## Tear Down (avoid AWS charges)

When you are done and have taken screenshots:

```bash
cd terraform/
terraform destroy
# Type: yes
```

This deletes the EC2, security group, key pair, and EBS volume.
**You will not be charged after this.**

---

## AMI Selection

Terraform auto-detects the latest Ubuntu 22.04 LTS AMI for the selected region.
Use `-var 'ami_id=ami-...'` only if you need to force a specific image.

---

## Troubleshooting

**SSH connection refused**
- Wait 60–90 seconds after `terraform apply` — EC2 is still booting
- Check the security group has port 22 open (it does by default in our config)

**Ansible "unreachable"**
- Check the IP in `inventory.ini` matches `terraform output instance_public_ip`
- Make sure the private key path is `~/.ssh/sre-key` (no `.pem` extension)

**Docker images take too long to build**
- t2.micro has 1 vCPU — building 6 images takes ~5–8 minutes, this is normal

**Port not accessible in browser**
- Make sure you are using `http://` not `https://`
- Double-check the port number exactly (e.g. Grafana is 52057, not 3000)
