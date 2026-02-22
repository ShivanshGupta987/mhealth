# Complete Docker Deployment Guide - mHealth Application
## Full Dockerization with One-Command Deployment

---

## 🎯 Deployment Overview

**Scenario**: You have all code on your **local Windows PC**. You will **transfer it to a remote Linux server** and deploy using Docker.

| Phase | Location | What You Do |
|-------|----------|-------------|
| **Preparation** | Local PC | Create Docker files, configure for production |
| **Transfer** | Local → Server | Git push or SCP/SFTP transfer |
| **Configuration** | Remote Server | Update .env with server-specific values |
| **Deployment** | Remote Server | `docker compose up -d --build` |

---

## 📋 **STEP-BY-STEP: Local PC → Remote Server**

### Phase 1: Prepare on Local PC (Windows)

**ON YOUR LOCAL PC** - Do these steps first:

```bash
# 1. Create all Docker files (see sections below)
# - backend/Dockerfile
# - backend/start.sh
# - frontend2/Dockerfile
# - frontend2/nginx.conf
# - All .dockerignore files

# 2. Create .env.example for reference
cd backend
# Copy the .env.example content from section below

# 3. DO NOT create actual .env yet (you'll do this on server)

# 4. Commit everything to Git
git add .
git commit -m "Add Docker configuration for production deployment"
git push origin main
```

---

### Phase 2: Transfer to Remote Server

**Choose ONE method**:

#### **Option A: Using Git (Recommended)**

```bash
# ON REMOTE SERVER:
ssh your-username@your-server-ip

# Clone repository
git clone <your-repository-url>
cd mhealth
```

#### **Option B: Using SCP/SFTP (If no Git)**

```bash
# ON YOUR LOCAL PC (PowerShell):
# Compress entire project (excluding unnecessary files)
Compress-Archive -Path D:\iitgn_study\thesis\mhealth\* -DestinationPath mhealth.zip

# Transfer to server
scp mhealth.zip your-username@your-server-ip:/home/your-username/

# ON REMOTE SERVER:
ssh your-username@your-server-ip
unzip mhealth.zip
cd mhealth
```

---

### Phase 3: Configure .env on Server

**ON REMOTE SERVER** - Now create .env with server-specific values:

```bash
cd backend
cp .env.example .env
nano .env
```

**🔴 CRITICAL: Change these values for server deployment:**

```env
# ========================================
# ⚠️ CHANGE THESE FROM LOCAL TO SERVER
# ========================================

# 1. Database Password (CHANGE FROM LOCAL)
POSTGRES_PASSWORD=your_production_secure_password_here
# ❌ DON'T use "password" or local dev password
# ✅ Generate: openssl rand -base64 32

# 2. JWT Secret (CHANGE - MUST BE DIFFERENT FROM LOCAL)
JWT_SECRET_KEY=your_production_jwt_secret_here
# ❌ DON'T use local dev secret
# ✅ Generate: openssl rand -hex 32

# 3. MinIO Password (CHANGE FROM LOCAL)
MINIO_ROOT_PASSWORD=your_production_minio_password_here
# ❌ DON'T use "minioadmin"
# ✅ Generate: openssl rand -base64 32

# 4. Frontend URL (CHANGE TO SERVER IP/DOMAIN)
FRONTEND_URL=http://your-server-ip-address
# ❌ DON'T use http://localhost
# ✅ Use http://192.168.x.x or http://your-domain.com

# 5. App Host (CHANGE TO SERVER DOMAIN)
APP_HOST=your-server-ip-or-domain.com
# ❌ DON'T use localhost
# ✅ Use your actual server IP or domain

# 6. Exotel Configuration (MUST BE REAL CREDENTIALS)
EXOTEL_SID=your_actual_exotel_sid
EXOTEL_API_KEY=your_actual_exotel_api_key
EXOTEL_API_TOKEN=your_actual_exotel_api_token
EXOTEL_PHONE_NUMBER=+91XXXXXXXXXX
EXOTEL_WEBHOOK_TOKEN=your_actual_webhook_token
EXOTEL_APP_ID=your_actual_app_id
# ⚠️ These MUST be your real Exotel production credentials

# 7. Email Configuration (MUST BE REAL)
SMTP_USER=your-production-email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
# ⚠️ Use app-specific password, not your Gmail password

# 8. pgAdmin Credentials (CHANGE FROM DEFAULT)
PGADMIN_EMAIL=admin@yourdomain.com
PGADMIN_PASSWORD=secure_pgadmin_password_here

# ========================================
# ✅ THESE CAN STAY THE SAME AS LOCAL
# ========================================

# RabbitMQ (can keep defaults or change)
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

# SMTP Server (usually same)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# MinIO User (can keep)
MINIO_ROOT_USER=minioadmin
```

---

### Phase 4: Deploy on Server

**ON REMOTE SERVER**:

```bash
# 1. Install Docker (if not already installed)
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker

# 2. Verify .env is configured
cd /home/your-username/mhealth/backend
cat .env  # Check values are correct

# 3. Deploy entire application
docker compose up -d --build

# 4. Check status
docker compose ps

# 5. View logs
docker compose logs -f
```

---

## 🔐 .env Configuration: Local vs Server

### **Local Development (Your PC)** 
❌ **DO NOT deploy with these values**

```env
POSTGRES_PASSWORD=password              # ❌ Weak password
JWT_SECRET_KEY=dev-secret-key           # ❌ Not secure
FRONTEND_URL=http://localhost           # ❌ Won't work on server
APP_HOST=localhost                      # ❌ Won't work for external access
EXOTEL_SID=test_sid                     # ❌ Might be test credentials
SMTP_USER=test@example.com              # ❌ Might be fake
```

### **Production Server (Remote)** 
✅ **MUST use these types of values**

```env
POSTGRES_PASSWORD=K7x9mP2nQ8vL4wR6tY3hB5nM9zX   # ✅ Strong generated password
JWT_SECRET_KEY=a7f3c9e1b4d6f8a2c5e7b9d1f3a5c7   # ✅ Random hex from openssl
FRONTEND_URL=http://192.168.1.100       # ✅ Actual server IP
APP_HOST=mhealth.yourschool.edu         # ✅ Real domain or IP
EXOTEL_SID=your_real_sid123             # ✅ Real Exotel account
SMTP_USER=mhealth@yourschool.edu        # ✅ Real email
```

---

## ⚙️ Generate Secure Values on Server

**ON REMOTE SERVER**, use these commands to generate secure credentials:

```bash
# Generate secure PostgreSQL password
openssl rand -base64 32
# Output: K7x9mP2nQ8vL4wR6tY3hB5nM9zXcVbN1qW

# Generate JWT secret key
openssl rand -hex 32
# Output: a7f3c9e1b4d6f8a2c5e7b9d1f3a5c7e9b1d3f5a7c9e1b3d5f7a9c1e3f5a7c9

# Generate MinIO password
openssl rand -base64 32
# Output: P9mK6nL4wQ8vR3tX5hY7bN2zM1cV9xB4qA

# Then paste these into your .env file
```

---

## 📋 **PRE-DEPLOYMENT CHECKLIST**

### ✅ On Local PC (Before Transfer)

- [ ] Created `backend/Dockerfile`
- [ ] Created `backend/start.sh` (and made executable: `chmod +x`)
- [ ] Created `frontend2/Dockerfile`
- [ ] Created `frontend2/nginx.conf`
- [ ] Created all `.dockerignore` files
- [ ] Created `backend/.env.example` (template only)
- [ ] Updated `backend/docker-compose.yml` with full configuration
- [ ] Added health check endpoint to `backend/app/main_exotel.py`
- [ ] Verified model files exist in `ml-service/model_store/`
- [ ] Committed all changes to Git (or prepared for SCP transfer)
- [ ] **DO NOT create .env yet** (will do on server)

### ✅ On Remote Server (After Transfer)

- [ ] Docker and Docker Compose installed
- [ ] Code transferred (via Git clone or SCP)
- [ ] Created `.env` from `.env.example`
- [ ] **Changed** POSTGRES_PASSWORD to secure value
- [ ] **Changed** JWT_SECRET_KEY to random hex
- [ ] **Changed** MINIO_ROOT_PASSWORD to secure value
- [ ] **Updated** FRONTEND_URL to server IP or domain
- [ ] **Updated** APP_HOST to server IP or domain
- [ ] **Added** real Exotel credentials (SID, API_KEY, API_TOKEN, etc.)
- [ ] **Added** real email credentials (SMTP_USER, SMTP_PASSWORD)
- [ ] **Changed** PGADMIN_PASSWORD to secure value
- [ ] Verified `.env` file has correct values (no localhost, no defaults)
- [ ] Configured firewall (allow ports 80, 8000, 8001)
- [ ] Ready to deploy: `docker compose up -d --build`

---

## 🚀 **QUICK START (When on Server)**

Once you've transferred code and configured .env:

```bash
# ON REMOTE SERVER:
cd /path/to/mhealth/backend

# Deploy
docker compose up -d --build

# Verify
docker compose ps
curl http://localhost:8000/health

# Access from browser
http://your-server-ip
```

---

## 🎯 What This Achieves

✅ **9 Services in Docker**: Backend API, Celery, Frontend, ML Service, PostgreSQL, RabbitMQ, MinIO, pgAdmin  
✅ **Automatic Migrations**: Database schema updates on startup  
✅ **Data Persistence**: All data safe in Docker volumes  
✅ **One Command Deploy**: `docker compose up -d`  
✅ **Production Ready**: Health checks, auto-restart, optimized images  

---

## 📦 Files You Need to Create

### 1. **backend/Dockerfile**

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc postgresql-client libpq-dev ffmpeg libsndfile1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./start.sh"]
```

---

### 2. **backend/start.sh**

```bash
#!/bin/bash
set -e

echo "mHealth Backend Starting (${SERVICE_TYPE:-api})..."

wait_for_postgres() {
    until pg_isready -h postgres -p 5432 -U postgres; do
        sleep 2
    done
    echo "✓ PostgreSQL ready"
}

if [ "${SERVICE_TYPE}" = "api" ]; then
    wait_for_postgres
    echo "Running migrations..."
    alembic upgrade head
    echo "Starting API..."
    exec uvicorn app.main_exotel:app --host 0.0.0.0 --port 8000

elif [ "${SERVICE_TYPE}" = "celery_worker" ]; then
    wait_for_postgres
    until curl -f http://backend-api:8000/health > /dev/null 2>&1; do
        sleep 3
    done
    echo "Starting Celery worker..."
    exec celery -A app.celery_config_exotel worker -l info

else
    wait_for_postgres
    alembic upgrade head
    exec uvicorn app.main_exotel:app --host 0.0.0.0 --port 8000
fi
```

**Make executable**: `chmod +x backend/start.sh`

---

### 3. **frontend2/Dockerfile**

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK CMD wget --quiet --tries=1 --spider http://localhost || exit 1
CMD ["nginx", "-g", "daemon off;"]
```

---

### 4. **frontend2/nginx.conf**

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # API proxy
    location /api/ {
        proxy_pass http://backend-api:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
}
```

---

### 5. **backend/.dockerignore**

```
__pycache__/
*.pyc
venv/
.env
.env.*
!.env.example
.git/
*.log
alembic/versions/__pycache__/
```

---

### 6. **frontend2/.dockerignore**

```
node_modules/
dist/
.env
.env.*
.git/
*.log
```

---

### 7. **ml-service/.dockerignore**

```
__pycache__/
venv/
.env
.git/
model_store/*.pth
model_store/*.pt
```

---

### 8. **backend/docker-compose.yml** (Complete)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: mhealth-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: mhealth
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - mhealth-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  rabbitmq:
    image: rabbitmq:3.12-management
    container_name: mhealth-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER:-guest}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS:-guest}
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - mhealth-network
    healthcheck:
      test: rabbitmq-diagnostics -q ping
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

  minio:
    image: minio/minio:latest
    container_name: mhealth-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    networks:
      - mhealth-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  ml-service:
    build:
      context: ../ml-service
      dockerfile: Dockerfile
    container_name: mhealth-ml-service
    environment:
      ML_SERVICE_HOST: 0.0.0.0
      ML_SERVICE_PORT: 8001
      SENTIMENT_MODEL_PATH: /app/model_store/best_model_state_legacy.pth
    ports:
      - "8001:8001"
    volumes:
      - ../ml-service/model_store:/app/model_store:ro
    networks:
      - mhealth-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped

  backend-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: mhealth-backend-api
    environment:
      SERVICE_TYPE: api
      POSTGRES_DB_URL: postgresql://postgres:${POSTGRES_PASSWORD:-password}@postgres:5432/mhealth
      RABBITMQ_URL: amqp://${RABBITMQ_USER:-guest}:${RABBITMQ_PASS:-guest}@rabbitmq:5672//
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD:-minioadmin}
      CONTAINER_NAME: recordings
      ML_SERVICE_URL: http://ml-service:8001
      EXOTEL_SID: ${EXOTEL_SID}
      EXOTEL_API_KEY: ${EXOTEL_API_KEY}
      EXOTEL_API_TOKEN: ${EXOTEL_API_TOKEN}
      EXOTEL_PHONE_NUMBER: ${EXOTEL_PHONE_NUMBER}
      EXOTEL_WEBHOOK_TOKEN: ${EXOTEL_WEBHOOK_TOKEN}
      EXOTEL_APP_ID: ${EXOTEL_APP_ID}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      SMTP_HOST: ${SMTP_HOST:-smtp.gmail.com}
      SMTP_PORT: ${SMTP_PORT:-587}
      SMTP_USER: ${SMTP_USER}
      SMTP_PASSWORD: ${SMTP_PASSWORD}
      FRONTEND_URL: ${FRONTEND_URL:-http://localhost}
      APP_HOST: ${APP_HOST:-localhost}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
      minio:
        condition: service_healthy
      ml-service:
        condition: service_healthy
    networks:
      - mhealth-network
    restart: unless-stopped

  backend-celery:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: mhealth-celery-worker
    environment:
      SERVICE_TYPE: celery_worker
      POSTGRES_DB_URL: postgresql://postgres:${POSTGRES_PASSWORD:-password}@postgres:5432/mhealth
      RABBITMQ_URL: amqp://${RABBITMQ_USER:-guest}:${RABBITMQ_PASS:-guest}@rabbitmq:5672//
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD:-minioadmin}
      CONTAINER_NAME: recordings
      ML_SERVICE_URL: http://ml-service:8001
      EXOTEL_SID: ${EXOTEL_SID}
      EXOTEL_API_KEY: ${EXOTEL_API_KEY}
      EXOTEL_API_TOKEN: ${EXOTEL_API_TOKEN}
      EXOTEL_PHONE_NUMBER: ${EXOTEL_PHONE_NUMBER}
      APP_HOST: ${APP_HOST:-localhost}
    depends_on:
      postgres:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
      ml-service:
        condition: service_healthy
      backend-api:
        condition: service_started
    networks:
      - mhealth-network
    restart: unless-stopped

  frontend:
    build:
      context: ../frontend2
      dockerfile: Dockerfile
    container_name: mhealth-frontend
    ports:
      - "80:80"
    depends_on:
      - backend-api
    networks:
      - mhealth-network
    restart: unless-stopped

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: mhealth-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL:-admin@mhealth.com}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD:-admin}
    ports:
      - "5050:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    depends_on:
      - postgres
    networks:
      - mhealth-network
    restart: unless-stopped

networks:
  mhealth-network:
    driver: bridge

volumes:
  postgres_data:
  rabbitmq_data:
  minio_data:
  pgadmin_data:
```

---

### 9. **backend/.env.example**

**This is a TEMPLATE file. Create it on your local PC, but the actual .env will be created ON THE SERVER.**

```env
# ========================================
# mHealth Environment Configuration
# ========================================
# 
# ⚠️ IMPORTANT: This is a TEMPLATE (.env.example)
# - Keep this file in Git for reference
# - On SERVER: Copy to .env and fill with REAL values
# - DO NOT commit actual .env to Git (contains secrets)
#
# 🔴 CRITICAL: Change these values when deploying to server
# ========================================

# Database
# 🔴 CHANGE: Generate with: openssl rand -base64 32
POSTGRES_PASSWORD=CHANGE_THIS_ON_SERVER

# RabbitMQ (can keep defaults or change for security)
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

# MinIO (S3-compatible storage)
MINIO_ROOT_USER=minioadmin
# 🔴 CHANGE: Generate with: openssl rand -base64 32
MINIO_ROOT_PASSWORD=CHANGE_THIS_ON_SERVER

# Exotel (Telephony Integration)
# 🔴 CHANGE: Use your REAL Exotel production credentials
EXOTEL_SID=your_real_exotel_sid_here
EXOTEL_API_KEY=your_real_exotel_api_key
EXOTEL_API_TOKEN=your_real_exotel_api_token
EXOTEL_PHONE_NUMBER=+91XXXXXXXXXX
EXOTEL_WEBHOOK_TOKEN=your_real_webhook_token
EXOTEL_APP_ID=your_real_app_id

# Authentication
# 🔴 CHANGE: Generate with: openssl rand -hex 32
JWT_SECRET_KEY=CHANGE_THIS_TO_RANDOM_HEX_ON_SERVER

# Email Configuration (for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
# 🔴 CHANGE: Your real production email
SMTP_USER=your-production-email@gmail.com
# 🔴 CHANGE: Your Gmail app-specific password
SMTP_PASSWORD=your_gmail_app_password

# Frontend URL (for email links and CORS)
# 🔴 CHANGE: Use your server's IP address or domain
# ❌ DON'T use: http://localhost (won't work on server)
# ✅ USE: http://192.168.1.100 or http://your-domain.com
FRONTEND_URL=http://your-server-ip-address

# Application Configuration
# 🔴 CHANGE: Use your server's IP address or domain
# ❌ DON'T use: localhost
# ✅ USE: your-server-ip or your-domain.com
APP_HOST=your-server-ip-or-domain

# pgAdmin (optional - for database management UI)
PGADMIN_EMAIL=admin@mhealth.com
# 🔴 CHANGE: Use a strong password (not "admin")
PGADMIN_PASSWORD=CHANGE_THIS_ON_SERVER

# ========================================
# Template Instructions:
# ========================================
# 1. On LOCAL PC: Create this as .env.example (commit to Git)
# 2. On SERVER: cp .env.example .env
# 3. On SERVER: Edit .env and replace all "CHANGE_THIS_ON_SERVER" values
# 4. On SERVER: Replace localhost URLs with actual server IP
# 5. On SERVER: Use real Exotel and email credentials
# 6. On SERVER: Generate secure passwords using openssl commands
# ========================================
```

**Quick reference - Values to generate on server**:
```bash
# Run these commands on server to get secure values:
openssl rand -base64 32  # For POSTGRES_PASSWORD
openssl rand -hex 32     # For JWT_SECRET_KEY  
openssl rand -base64 32  # For MINIO_ROOT_PASSWORD
openssl rand -base64 20  # For PGADMIN_PASSWORD
```

---

### 10. Add Health Check to Backend

**Edit `backend/app/main_exotel.py`**, add this endpoint:

```python
from sqlalchemy import text
from app.sql_db import SessionLocal

@app.get("/health")
async def health_check():
    """Health check for Docker"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "healthy",
            "service": "backend-api",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

---

## 🚀 Server Deployment Instructions

**⚠️ These steps are performed ON YOUR REMOTE SERVER (not local PC)**

### 1. Install Docker on Server

**SSH into your server first**:
```bash
ssh your-username@your-server-ip
```

**Then install Docker**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### 2. Transfer Code to Server

**Option A: Clone from Git (Recommended)**
```bash
# On server
git clone <your-repository-url>
cd mhealth
```

**Option B: Transfer via SCP (If no Git)**
```bash
# On your local PC (PowerShell):
scp -r D:\iitgn_study\thesis\mhealth your-username@your-server-ip:/home/your-username/

# Then SSH to server:
ssh your-username@your-server-ip
cd /home/your-username/mhealth
```

### 3. Verify All Files Exist

```bash
# Check all Docker files are present
ls backend/Dockerfile
ls backend/start.sh
ls frontend2/Dockerfile
ls frontend2/nginx.conf
ls backend/docker-compose.yml

# Check model file exists
ls ml-service/model_store/best_model_state_legacy.pth

# If start.sh is not executable:
chmod +x backend/start.sh
```

### 4. Configure Environment for Production

**⚠️ CRITICAL STEP - Configure .env for server**:

```bash
cd backend

# Create .env from template
cp .env.example .env

# Edit with server-specific values
nano .env
cp .env.example .env
nano .env

# REQUIRED: Change these values
POSTGRES_PASSWORD=your_secure_db_password
JWT_SECRET_KEY=$(openssl rand -hex 32)
MINIO_ROOT_PASSWORD=your_minio_password

# Add your Exotel credentials
EXOTEL_SID=...
EXOTEL_API_KEY=...
EXOTEL_API_TOKEN=...
EXOTEL_PHONE_NUMBER=...

# Add email config
SMTP_USER=...
SMTP_PASSWORD=...

# Set server details
FRONTEND_URL=http://your-server-ip
APP_HOST=your-domain.com
```

### 5. Deploy

```bash
cd backend

# Build and start all services
docker compose up -d --build
```

**Expected output**:
```
[+] Running 10/10
 ✔ Network mhealth-network Created
 ✔ Container mhealth-postgres Started
 ✔ Container mhealth-rabbitmq Started
 ✔ Container mhealth-minio Started
 ✔ Container mhealth-ml-service Started
 ✔ Container mhealth-backend-api Started
 ✔ Container mhealth-celery-worker Started
 ✔ Container mhealth-frontend Started
 ✔ Container mhealth-pgadmin Started
```

### 6. Verify Deployment

```bash
# Check container status
docker compose ps

# All should show "Up" and "(healthy)"
# View logs
docker compose logs -f

# Test endpoints
curl http://localhost:8000/health
# {"status":"healthy","database":"connected"}

curl http://localhost:8001/health
# {"status":"healthy"}

# Access in browser
http://your-server-ip          # Frontend
http://your-server-ip:8000/docs # API docs
http://your-server-ip:15672    # RabbitMQ
http://your-server-ip:9001     # MinIO
```

---

## ✅ Success Checklist

After deployment, verify:

- [ ] `docker compose ps` shows all 9 containers running
- [ ] All health checks are "healthy"
- [ ] Frontend loads at http://server-ip
- [ ] Can login to frontend
- [ ] Backend API responds: `curl http://localhost:8000/health`
- [ ] ML Service responds: `curl http://localhost:8001/health`
- [ ] Migrations completed: `docker compose logs backend-api | grep "Migrations completed"`
- [ ] Celery worker running: `docker compose logs backend-celery | grep "celery@.* ready"`
- [ ] Data persists after restart: `docker compose down && docker compose up -d`

---

## 💾 Data Persistence & Backups

### Understanding Data Safety

Your data is in **Docker volumes** (on server disk):
```
/var/lib/docker/volumes/mhealth_postgres_data/  ← Database
/var/lib/docker/volumes/mhealth_minio_data/     ← Recordings
```

**Data survives**:
- ✅ `docker compose down` (stops containers)
- ✅ `docker compose restart`
- ✅ Rebuilding images
- ✅ Server reboots

**Data lost only with**:
- ❌ `docker compose down -v` (deletes volumes explicitly)
- ❌ `docker volume rm` (manual deletion)
- ❌ Disk failure

### Automated Backup Script

**Create `backup.sh`**:

```bash
#!/bin/bash
BACKUP_DIR="/backup/mhealth"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker exec mhealth-postgres pg_dump -U postgres mhealth > $BACKUP_DIR/db_$DATE.sql
gz ip $BACKUP_DIR/db_$DATE.sql

# Delete backups older than 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_$DATE.sql.gz"
```

**Schedule daily backups**:
```bash
chmod +x backup.sh
crontab -e

# Add:
0 2 * * * /path/to/backup.sh >> /var/log/mhealth-backup.log 2>&1
```

### Restore from Backup

```bash
# Decompress backup
gunzip mhealth_backup.sql.gz

# Restore to PostgreSQL
docker exec -i mhealth-postgres psql -U postgres mhealth < mhealth_backup.sql
```

---

## 🔄 Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
cd backend
docker compose up -d --build

# Migrations run automatically on startup
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend-api
docker compose logs -f backend-celery
docker compose logs -f ml-service

# Last 100 lines
docker compose logs --tail=100 backend-api
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend-api

# Stop all (keeps data)
docker compose stop

# Stop and remove containers (keeps data)
docker compose down

# Complete cleanup (⚠️ deletes data!)
docker compose down -v
```

---

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker compose logs backend-api

# Common issues:
# 1. PostgreSQL not ready → Wait, auto-retry
# 2. Migration failed → Check alembic logs
# 3. Missing env vars → Check .env file

# Manual migration
docker exec -it mhealth-backend-api bash
alembic upgrade head
```

### Frontend Shows 404 for API

```bash
# Check Nginx config
docker exec mhealth-frontend cat /etc/nginx/conf.d/default.conf

# Test backend from frontend container
docker exec mhealth-frontend wget -O- http://backend-api:8000/health

# Restart frontend
docker compose restart frontend
```

### ML Service Model Error

```bash
# Check model file exists
docker exec mhealth-ml-service ls -lh /app/model_store/

# Verify mount
docker inspect mhealth-ml-service | grep -A 10 Mounts

# Copy model if missing
cp backend/model_store/best_model_state_legacy.pth ml-service/model_store/

# Restart
docker compose restart ml-service
```

### Celery Not Processing Tasks

```bash
# Check Celery logs
docker compose logs backend-celery

# Check RabbitMQ
docker compose logs rabbitmq

# Restart Celery
docker compose restart backend-celery

# Verify connection
docker exec mhealth-celery-worker celery -A app.celery_config_exotel inspect ping
```

---

## 🔐 Production Security

### Before Going Live

```bash
# 1. Change ALL default passwords in .env
POSTGRES_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
MINIO_ROOT_PASSWORD=$(openssl rand -base64 32)

# 2. Configure firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable

# 3. Set up SSL with Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# 4. Configure Docker log rotation
sudo nano /etc/docker/daemon.json
# Add:
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
sudo systemctl restart docker
```

---

## 📊 Resource Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Disk | 50 GB SSD | 100 GB SSD |
| Network | 100 Mbps | 1 Gbps |

---

## 📞 Quick Reference

### Common Commands

```bash
# Deploy
docker compose up -d --build

# Status
docker compose ps

# Logs
docker compose logs -f [service]

# Restart
docker compose restart [service]

# Stop
docker compose down

# Backup database
docker exec mhealth-postgres pg_dump -U postgres mhealth > backup.sql

# Connect to database
docker exec -it mhealth-postgres psql -U postgres -d mhealth

# Shell into container
docker exec -it mhealth-backend-api bash

# View resource usage
docker stats
```

---

## 📋 COMPLETE WORKFLOW SUMMARY: Local PC → Server Deployment

### **Phase 1: Prepare on Local PC (Windows)**

**What to do on your local machine**:

1. ✅ Create all Docker files (sections above):
   - `backend/Dockerfile`
   - `backend/start.sh` 
   - `frontend2/Dockerfile`
   - `frontend2/nginx.conf`
   - `.dockerignore` files
   - Update `docker-compose.yml`
   - Add health check to `main_exotel.py`

2. ✅ Create `.env.example` (template only, not actual `.env`)

3. ✅ Commit to Git:
   ```bash
   git add .
   git commit -m "Add Docker production configuration"
   git push origin main
   ```

4. ❌ **DO NOT** create actual `.env` file locally (will do on server)

---

### **Phase 2: Transfer to Server**

**Choose one method**:

```bash
# Method A: Git (Recommended)
# On server:
git clone <your-repo-url>

# Method B: SCP (Alternative)
# On local PC:
scp -r D:\iitgn_study\thesis\mhealth user@server-ip:/home/user/
```

---

### **Phase 3: Configure .env on Server**

**ON SERVER - Create and configure .env**:

```bash
cd backend
cp .env.example .env
nano .env
```

**🔴 MANDATORY CHANGES in .env (from local to server)**:

| Variable | Local (DON'T USE) | Server (MUST USE) |
|----------|-------------------|-------------------|
| `POSTGRES_PASSWORD` | `password` | Generate: `openssl rand -base64 32` |
| `JWT_SECRET_KEY` | `dev-secret` | Generate: `openssl rand -hex 32` |
| `MINIO_ROOT_PASSWORD` | `minioadmin` | Generate: `openssl rand -base64 32` |
| `FRONTEND_URL` | `http://localhost` | `http://192.168.1.100` (your server IP) |
| `APP_HOST` | `localhost` | `your-server-ip` or `domain.com` |
| `EXOTEL_SID` | test credentials | **Real Exotel production SID** |
| `EXOTEL_API_KEY` | test credentials | **Real Exotel API Key** |
| `EXOTEL_API_TOKEN` | test credentials | **Real Exotel API Token** |
| `EXOTEL_PHONE_NUMBER` | test number | **Real Exotel phone number** |
| `SMTP_USER` | test email | **Real production email** |
| `SMTP_PASSWORD` | test password | **Real Gmail app password** |
| `PGADMIN_PASSWORD` | `admin` | Strong unique password |

**Generate secure values**:
```bash
# On server, run these:
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)"
echo "MINIO_ROOT_PASSWORD=$(openssl rand -base64 32)"

# Copy the output and paste into .env
```

---

### **Phase 4: Deploy on Server**

```bash
# 1. Install Docker (if needed)
sudo apt install -y docker.io docker-compose-plugin

# 2. Deploy
cd backend
docker compose up -d --build

# 3. Verify
docker compose ps
curl http://localhost:8000/health

# 4. Access from browser
http://your-server-ip
```

---

## ⚡ Quick Copy-Paste Commands for Server

**Complete server deployment sequence**:

```bash
# 1. SSH to server
ssh your-username@your-server-ip

# 2. Install Docker
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo systemctl start docker && sudo systemctl enable docker
sudo usermod -aG docker $USER && newgrp docker

# 3. Clone code
git clone <your-repo-url>
cd mhealth

# 4. Make start.sh executable
chmod +x backend/start.sh

# 5. Configure environment
cd backend
cp .env.example .env
nano .env  # Edit with values from table above

# 6. Generate secure passwords
openssl rand -base64 32  # For PostgreSQL
openssl rand -hex 32     # For JWT
openssl rand -base64 32  # For MinIO

# 7. Deploy
docker compose up -d --build

# 8. Check status
docker compose ps
docker compose logs -f

# 9. Test endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health

# 10. Access from your browser
# http://your-server-ip
```

---

## 🔐 Final .env Checklist (Server)

Before running `docker compose up -d --build`, verify your `.env` has:

- [ ] `POSTGRES_PASSWORD` = Secure random password (NOT "password")
- [ ] `JWT_SECRET_KEY` = 64-character hex string (NOT "dev-secret")
- [ ] `MINIO_ROOT_PASSWORD` = Secure random password (NOT "minioadmin")
- [ ] `FRONTEND_URL` = `http://your-actual-server-ip` (NOT localhost)
- [ ] `APP_HOST` = Your server IP or domain (NOT localhost)
- [ ] `EXOTEL_SID` = Your real Exotel account SID
- [ ] `EXOTEL_API_KEY` = Your real Exotel API key
- [ ] `EXOTEL_API_TOKEN` = Your real Exotel API token
- [ ] `EXOTEL_PHONE_NUMBER` = Your real Exotel phone number
- [ ] `EXOTEL_WEBHOOK_TOKEN` = Your real webhook token
- [ ] `EXOTEL_APP_ID` = Your real Exotel app ID
- [ ] `SMTP_USER` = Your real production email
- [ ] `SMTP_PASSWORD` = Your real Gmail app-specific password
- [ ] `PGADMIN_PASSWORD` = Strong password (NOT "admin")

**If all checked ✅, you're ready to deploy!**

---

## 🎯 Summary

**You now have**:
- ✅ Complete workflow: Local PC → Remote Server
- ✅ Clear distinction: What to do locally vs on server
- ✅ Exact list of .env variables to change
- ✅ All 9 services containerized
- ✅ One-command deployment
- ✅ Automatic database migrations
- ✅ Persistent data with volumes
- ✅ Production-ready configuration
- ✅ Backup strategy
- ✅ Troubleshooting guide

**Deploy command (on server)**:
```bash
docker compose up -d --build
```

**That's it!** Your entire mHealth application runs in Docker with data safety, auto-restart, and easy updates.

---

**Last Updated**: February 14, 2026  
**Version**: 2.0 - Full Dockerization (Local → Server Deployment)  
**Status**: ✅ Ready for Implementation
