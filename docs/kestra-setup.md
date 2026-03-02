# Kestra Setup Guide

## Prerequisites

- A VPS or server with at least 2 CPU, 4GB RAM, 50GB disk
- Docker and Docker Compose installed
- Domain or IP address for Kestra UI access

## Quick Start (Docker Compose)

### 1. Create a directory on your server

```bash
mkdir -p /opt/kestra && cd /opt/kestra
```

### 2. Create docker-compose.yml

```yaml
version: "3.8"

services:
  kestra:
    image: kestra/kestra:latest
    pull_policy: always
    user: "root"
    command: server standalone
    volumes:
      - kestra-data:/app/storage
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/kestra-wd:/tmp/kestra-wd
      - /opt/kestra/lancedb:/data/lancedb
    environment:
      KESTRA_CONFIGURATION: |
        datasources:
          postgres:
            url: jdbc:postgresql://postgres:5432/kestra
            driverClassName: org.postgresql.Driver
            username: kestra
            password: ${KESTRA_DB_PASSWORD}
        kestra:
          server:
            basic-auth:
              enabled: true
              username: admin
              password: ${KESTRA_ADMIN_PASSWORD}
          repository:
            type: postgres
          storage:
            type: local
            local:
              base-path: "/app/storage"
          queue:
            type: postgres
    ports:
      - "8080:8080"
      - "8081:8081"
    depends_on:
      postgres:
        condition: service_started

  postgres:
    image: postgres:16
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: kestra
      POSTGRES_USER: kestra
      POSTGRES_PASSWORD: ${KESTRA_DB_PASSWORD}

volumes:
  kestra-data:
  postgres-data:
```

### 3. Create .env file

```bash
KESTRA_DB_PASSWORD=your_secure_password_here
KESTRA_ADMIN_PASSWORD=your_admin_password_here
```

### 4. Start Kestra

```bash
docker compose up -d
```

### 5. Access Kestra UI

Navigate to `http://your-server-ip:8080`

## Setting Up Secrets

In the Kestra UI, go to **Administration → Secrets** and add:

| Key | Description |
|-----|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key for training data generation |
| `RUNPOD_API_KEY` | RunPod API key for GPU rental |
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API key (free) |
| `MODEL_API_URL` | URL of your deployed fine-tuned model |
| `SLACK_WEBHOOK` | (Optional) Slack webhook for notifications |

## Importing Flows

Upload all YAML files from `kestra-flows/` directory via the Kestra UI:
1. Go to **Flows**
2. Click **Create**
3. Paste the YAML content
4. Click **Save**

Or use the Kestra CLI:
```bash
kestra flow namespace update ols-research kestra-flows/ --server=http://localhost:8080
```

## LanceDB Data Directory

LanceDB data is stored at `/opt/kestra/lancedb` on the host, mounted into containers at `/data/lancedb`. This directory persists across container restarts and should be included in your backup strategy.

## Next Steps

After Kestra is running:
1. Import collection flows first
2. Run `collect-openalex` manually to test
3. Verify data appears in storage
4. Import processing flows
5. Continue through the build sequence in `docs/architecture.md`
