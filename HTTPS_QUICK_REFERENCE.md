# HTTPS Quick Reference - mHealth

## 🚀 Quick Setup (Self-Signed Certificate)

### From Windows (Your PC):

```powershell
cd D:\iitgn_study\thesis\mhealth
.\setup-ssl.ps1
```

### From Server:

```bash
ssh -p 2022 shivansh.gupta@10.0.62.206
cd ~/mhealth
chmod +x setup-ssl.sh
./setup-ssl.sh
```

### Update .env and Deploy:

```bash
# On server
cd ~/mhealth/backend
nano .env

# Update this line:
FRONTEND_URL=https://mhealth.iitgn.ac.in,https://10.0.62.206

# Save and restart
docker compose down
docker compose up -d --build
```

### Access:

- **HTTPS**: https://mhealth.iitgn.ac.in
- **Backend**: https://mhealth.iitgn.ac.in:8000 (if needed)

---

## 📋 What Was Changed:

1. **nginx.conf**: Added HTTPS listener on port 443, HTTP→HTTPS redirect
2. **docker-compose.yml**: Exposed port 443, added SSL volume mount
3. **.env.example**: Updated FRONTEND_URL to use https://
4. **client.ts**: Auto-detects http/https from current page

---

## 🔧 Manual Certificate Generation (Server):

```bash
# SSH to server
ssh -p 2022 shivansh.gupta@10.0.62.206

# Navigate to project
cd ~/mhealth/backend

# Create SSL directory
mkdir -p ssl

# Generate self-signed certificate (1 year validity)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/C=IN/ST=Gujarat/L=Gandhinagar/O=IIT Gandhinagar/OU=mHealth/CN=mhealth.iitgn.ac.in"

# Set permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

# Update .env
nano .env
# Update: FRONTEND_URL=https://mhealth.iitgn.ac.in,https://10.0.62.206

# Deploy
docker compose down
docker compose up -d --build
```

---

## 🌐 Let's Encrypt (Production):

```bash
# Install certbot
sudo apt install -y certbot

# Stop frontend temporarily
cd ~/mhealth/backend
docker compose stop frontend

# Get certificate
sudo certbot certonly --standalone \
  -d mhealth.iitgn.ac.in \
  --email your-email@iitgn.ac.in \
  --agree-tos

# Copy to project
mkdir -p ssl
sudo cp /etc/letsencrypt/live/mhealth.iitgn.ac.in/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/mhealth.iitgn.ac.in/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*.pem
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

# Start services
docker compose up -d --build
```

---

## ✅ Verification:

```bash
# Test HTTPS
curl -I https://mhealth.iitgn.ac.in

# Test HTTP redirect
curl -I http://mhealth.iitgn.ac.in

# Check certificate
openssl s_client -connect mhealth.iitgn.ac.in:443 -servername mhealth.iitgn.ac.in

# View logs
docker compose logs -f frontend
```

---

## 🔒 Security Notes:

- **Self-Signed**: Browsers show warning (normal for testing)
- **Let's Encrypt**: Trusted certificate, no warnings
- **Certificates**: Valid for 365 days (self-signed) or 90 days (Let's Encrypt)
- **Auto-Renewal**: Set up cron job for Let's Encrypt

---

## 🐛 Troubleshooting:

### Can't access HTTPS:
```bash
# Check if port 443 is open
sudo ufw status
sudo ufw allow 443/tcp

# Check if container is listening
docker exec mhealth-frontend netstat -tulpn | grep 443

# Check logs
docker compose logs frontend
```

### Certificate errors:
```bash
# Verify certificate exists
ls -la ~/mhealth/backend/ssl/

# Check inside container
docker exec mhealth-frontend ls -la /etc/nginx/ssl/

# Verify certificate validity
openssl x509 -in ssl/cert.pem -text -noout
```

### Browser shows "Not Secure":
- **Self-signed**: Expected - click "Advanced" → "Proceed"
- **Let's Encrypt**: Check certificate installation
- **Mixed content**: Ensure all resources load via HTTPS

---

## 📚 Full Documentation:

See [SSL_SETUP_GUIDE.md](SSL_SETUP_GUIDE.md) for complete instructions.
