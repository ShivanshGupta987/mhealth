# QUICK DEPLOYMENT REFERENCE - mHealth Docker

## 📍 Current State
- ✅ All code on LOCAL PC (Windows): `D:\iitgn_study\thesis\mhealth`
- 🎯 Target: Deploy to REMOTE SERVER (Linux)

---

## 🚀 3-PHASE DEPLOYMENT

### PHASE 1: Prepare Locally (On Your PC)

```bash
# Already done - your code is ready!
# Just make sure you have:
✅ All Docker files created
✅ Committed to Git (or ready to transfer via SCP)
❌ DO NOT create .env locally
```

---

### PHASE 2: Transfer to Server

**Choose ONE method**:

```bash
# METHOD A: Git (Recommended)
ssh user@server-ip
git clone <your-repo-url>
cd mhealth

# METHOD B: SCP (Alternative)  
# On local PC PowerShell:
scp -r D:\iitgn_study\thesis\mhealth user@server-ip:/home/user/
```

---

### PHASE 3: Deploy on Server

```bash
# 1. SSH to server
ssh your-username@your-server-ip

# 2. Install Docker (if not installed)
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker

# 3. Navigate to project
cd /home/your-username/mhealth

# 4. Make script executable
chmod +x backend/start.sh

# 5. Create .env from template
cp backend/.env.example backend/.env

# 6. Generate secure values
openssl rand -base64 32  # Copy for POSTGRES_PASSWORD
openssl rand -hex 32     # Copy for JWT_SECRET_KEY
openssl rand -base64 32  # Copy for MINIO_ROOT_PASSWORD

# 7. Edit .env with values from table below
nano backend/.env

# 8. Deploy!
docker compose up -d --build

# 9. Verify
docker compose ps
curl http://localhost:8000/health
```

---

## 🔐 .env VALUES TO CHANGE

| Variable | What to Put | How to Get It |
|----------|-------------|---------------|
| `POSTGRES_PASSWORD` | Random secure password | `openssl rand -base64 32` |
| `JWT_SECRET_KEY` | Random 64-char hex | `openssl rand -hex 32` |
| `MINIO_ROOT_PASSWORD` | Random secure password | `openssl rand -base64 32` |
| `FRONTEND_URL` | Server URL | `http://mhealth.iitgn.ac.in` or `http://192.168.1.100` |
| `APP_HOST` | Server domain or IP | `mhealth.iitgn.ac.in` or `192.168.1.100` |
| `EXOTEL_SID` | Real Exotel SID | From your Exotel dashboard |
| `EXOTEL_API_KEY` | Real API Key | From your Exotel dashboard |
| `EXOTEL_API_TOKEN` | Real API Token | From your Exotel dashboard |
| `EXOTEL_PHONE_NUMBER` | Real phone number | `+91XXXXXXXXXX` |
| `EXOTEL_WEBHOOK_TOKEN` | Real webhook token | From your Exotel dashboard |
| `EXOTEL_APP_ID` | Real app ID | From your Exotel dashboard |
| `SMTP_USER` | Production email | `mhealth@yourschool.edu` |
| `SMTP_PASSWORD` | Gmail app password | Google Account → Security → App passwords |
| `PGADMIN_PASSWORD` | Strong password | Create your own |

---

## ⚠️ CRITICAL: Don't Use These Values on Server

| Variable | ❌ DON'T USE | ✅ USE INSTEAD |
|----------|--------------|----------------|
| `POSTGRES_PASSWORD` | `password` | Generated random (32+ chars) |
| `JWT_SECRET_KEY` | `dev-secret` | `openssl rand -hex 32` output |
| `FRONTEND_URL` | `http://localhost` | `http://your-server-ip` |
| `APP_HOST` | `localhost` | Your actual server IP or domain |
| `MINIO_ROOT_PASSWORD` | `minioadmin` | Generated random (32+ chars) |

---

## ✅ Final Checklist Before Deploy

**Before running `docker compose up -d --build`, verify**:

- [ ] SSH'd into server
- [ ] Docker installed (`docker --version` works)
- [ ] Code transferred to server
- [ ] Created `.env` from `.env.example`
- [ ] Changed `POSTGRES_PASSWORD` to secure value
- [ ] Changed `JWT_SECRET_KEY` to random hex
- [ ] Changed `MINIO_ROOT_PASSWORD` to secure value
- [ ] Updated `FRONTEND_URL` to server IP (not localhost)
- [ ] Updated `APP_HOST` to server IP (not localhost)
- [ ] Added real Exotel credentials (all 6 values)
- [ ] Added real email credentials
- [ ] Changed `PGADMIN_PASSWORD` to secure value
- [ ] Saved .env file

**If all checked, run**: `docker compose up -d --build`

---

## 🎯 After Deployment

```bash
# Check all containers running
docker compose ps
# Expected: All 9 services "Up (healthy)"

# Test backend
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Test ML service
curl http://localhost:8001/health
# Expected: {"status":"healthy"}

# View logs
docker compose logs -f

# Access from browser (from your laptop)
http://your-server-ip         # Frontend
http://your-server-ip:8000/docs  # API docs
```

---

## 🐛 Quick Troubleshooting

**Container won't start?**
```bash
docker compose logs <service-name>
```

**Database connection error?**
```bash
docker compose logs postgres
docker compose logs backend-api
```

**Frontend can't reach backend?**
```bash
# Check nginx config
docker exec mhealth-frontend cat /etc/nginx/conf.d/default.conf

# Restart frontend
docker compose restart frontend
```

**Need to update code?**
```bash
git pull origin main
docker compose up -d --build
```

---

## 📞 Get Server IP Address

```bash
# On server, run:
hostname -I
# Or:
ip addr show | grep "inet " | grep -v 127.0.0.1
```

Use this IP for `FRONTEND_URL` and `APP_HOST` in .env

---

## 🔄 Update Application

```bash
# SSH to server
ssh user@server-ip

# Pull latest code
cd /home/user/mhealth
git pull origin main

# Rebuild and restart
docker compose up -d --build

# Check status
docker compose ps
docker compose logs -f
```

---

**That's it! Print this page and keep it handy during deployment.**
