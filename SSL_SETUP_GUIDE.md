# HTTPS/SSL Setup Guide for mHealth Application

This guide covers enabling HTTPS for your mHealth application.

---

## Prerequisites

- Docker deployment running successfully
- Domain name configured: `mhealth.iitgn.ac.in`
- Port 443 accessible (firewall rules configured)
- SSH access to server

---

## Option 1: Self-Signed Certificates (For Testing/Internal Use)

Use this for testing or internal networks where you don't need a trusted certificate.

### Generate Self-Signed Certificate

SSH to your server and run:

```bash
ssh -p 2022 shivansh.gupta@10.0.62.206

# Navigate to project
cd /home/shivansh.gupta/mhealth/backend

# Create SSL directory
mkdir -p ssl

# Generate self-signed certificate (valid for 1 year)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/C=IN/ST=Gujarat/L=Gandhinagar/O=IIT Gandhinagar/OU=mHealth/CN=mhealth.iitgn.ac.in"

# Set proper permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

# Verify certificate
openssl x509 -in ssl/cert.pem -text -noout
```

### Update .env File

```bash
nano .env
```

Update `FRONTEND_URL`:

```env
FRONTEND_URL=https://mhealth.iitgn.ac.in,https://10.0.62.206,http://mhealth.iitgn.ac.in,http://10.0.62.206
```

### Deploy with HTTPS

```bash
# Restart services
docker compose down
docker compose up -d --build

# Check logs
docker compose logs -f frontend
```

### Access Your Application

- HTTPS: `https://mhealth.iitgn.ac.in` (will show security warning - this is normal for self-signed)
- HTTP: Automatically redirects to HTTPS

**Note:** Browsers will show a security warning for self-signed certificates. Click "Advanced" → "Proceed to site" to continue.

---

## Option 2: Let's Encrypt (For Production - Free Trusted Certificate)

Use this for production deployments with a public domain.

### Prerequisites for Let's Encrypt

- Public domain name (`mhealth.iitgn.ac.in`) must resolve to your server's public IP
- Port 80 and 443 must be accessible from the internet
- Server must be publicly accessible

### Install Certbot

```bash
ssh -p 2022 shivansh.gupta@10.0.62.206

# Update system
sudo apt update

# Install certbot
sudo apt install -y certbot

# Or using snap (recommended)
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

### Temporarily Stop Frontend for Certificate Generation

```bash
cd /home/shivansh.gupta/mhealth/backend
docker compose stop frontend
```

### Generate Let's Encrypt Certificate

```bash
# Replace with your actual email
sudo certbot certonly --standalone \
  -d mhealth.iitgn.ac.in \
  --email your-email@iitgn.ac.in \
  --agree-tos \
  --non-interactive

# Certificate will be saved at:
# /etc/letsencrypt/live/mhealth.iitgn.ac.in/fullchain.pem
# /etc/letsencrypt/live/mhealth.iitgn.ac.in/privkey.pem
```

### Copy Certificates to Project

```bash
cd /home/shivansh.gupta/mhealth/backend

# Create SSL directory
mkdir -p ssl

# Copy certificates (with sudo)
sudo cp /etc/letsencrypt/live/mhealth.iitgn.ac.in/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/mhealth.iitgn.ac.in/privkey.pem ssl/key.pem

# Change ownership to your user
sudo chown $USER:$USER ssl/*.pem

# Set proper permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem
```

### Update .env File

```bash
nano .env
```

Update `FRONTEND_URL`:

```env
FRONTEND_URL=https://mhealth.iitgn.ac.in,http://mhealth.iitgn.ac.in
```

### Deploy with HTTPS

```bash
# Start all services
docker compose up -d --build

# Check logs
docker compose logs -f frontend
```

### Set Up Auto-Renewal

Let's Encrypt certificates expire every 90 days. Set up auto-renewal:

```bash
# Test renewal
sudo certbot renew --dry-run

# Add renewal script
sudo crontab -e

# Add this line to renew daily and copy to project
0 2 * * * certbot renew --quiet && cp /etc/letsencrypt/live/mhealth.iitgn.ac.in/fullchain.pem /home/shivansh.gupta/mhealth/backend/ssl/cert.pem && cp /etc/letsencrypt/live/mhealth.iitgn.ac.in/privkey.pem /home/shivansh.gupta/mhealth/backend/ssl/key.pem && docker restart mhealth-frontend
```

---

## Option 3: Manual Certificate (If You Have Existing Certificate)

If you already have SSL certificates from your organization:

```bash
cd /home/shivansh.gupta/mhealth/backend

# Create SSL directory
mkdir -p ssl

# Upload your certificate and key
# Use SCP from your local machine:
scp -P 2022 /path/to/your/certificate.crt shivansh.gupta@10.0.62.206:/home/shivansh.gupta/mhealth/backend/ssl/cert.pem
scp -P 2022 /path/to/your/private.key shivansh.gupta@10.0.62.206:/home/shivansh.gupta/mhealth/backend/ssl/key.pem

# Set permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem
```

Then follow the deployment steps from Option 1.

---

## Verification

After deployment, verify HTTPS is working:

```bash
# Test HTTPS connection
curl -I https://mhealth.iitgn.ac.in

# Test HTTP redirect
curl -I http://mhealth.iitgn.ac.in

# Check certificate details
openssl s_client -connect mhealth.iitgn.ac.in:443 -servername mhealth.iitgn.ac.in
```

### Browser Testing

1. Open `https://mhealth.iitgn.ac.in`
2. Check for secure padlock icon in address bar
3. Click padlock → Certificate → Verify details
4. Ensure HTTP automatically redirects to HTTPS

---

## Firewall Configuration

Make sure ports are open:

```bash
# Check firewall status
sudo ufw status

# Allow HTTPS if needed
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp

# Or for iptables
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
```

---

## Troubleshooting

### Issue: "Connection refused" on port 443

```bash
# Check if port 443 is exposed
docker compose ps

# Check if nginx is listening
docker exec mhealth-frontend netstat -tulpn | grep 443

# Check frontend logs
docker compose logs frontend
```

### Issue: Certificate not found error

```bash
# Verify certificates exist
ls -la /home/shivansh.gupta/mhealth/backend/ssl/

# Check permissions
docker exec mhealth-frontend ls -la /etc/nginx/ssl/

# Verify certificate validity
openssl x509 -in ./ssl/cert.pem -text -noout
```

### Issue: "SSL handshake failed"

```bash
# Check certificate and key match
openssl x509 -noout -modulus -in ssl/cert.pem | openssl md5
openssl rsa -noout -modulus -in ssl/key.pem | openssl md5
# Output should be identical
```

### Issue: Browser shows "Not Secure" (Self-Signed)

This is expected with self-signed certificates. Options:

1. Add exception in browser (for testing)
2. Use Let's Encrypt for trusted certificate
3. Add certificate to system trust store (for internal use)

### Issue: Let's Encrypt validation fails

```bash
# Ensure domain resolves to server
nslookup mhealth.iitgn.ac.in

# Ensure port 80 is accessible from internet
# Test from external machine:
curl http://mhealth.iitgn.ac.in

# Check certbot logs
sudo journalctl -u certbot
```

---

## Backend API HTTPS (Optional)

The backend API currently runs on HTTP (port 8000). For full HTTPS:

### Option A: Access via Frontend Proxy (Recommended)

Use nginx to proxy API requests:

- Frontend: `https://mhealth.iitgn.ac.in/`
- API via proxy: `https://mhealth.iitgn.ac.in/api/`

### Option B: Separate HTTPS for Backend (Advanced)

Requires separate nginx container or load balancer for backend.

---

## Security Best Practices

1. **Use Strong Cipher Suites**: Already configured in nginx.conf
2. **Enable HTTP Strict Transport Security (HSTS)**: Add to nginx.conf
3. **Regular Certificate Renewal**: Set up auto-renewal for Let's Encrypt
4. **Keep Private Key Secure**:
   - Never commit to Git
   - Set proper permissions (600)
   - Backup securely
5. **Monitor Certificate Expiry**: Set up alerts

---

## Quick Commands Reference

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ssl/key.pem -out ssl/cert.pem -subj "/CN=mhealth.iitgn.ac.in"

# Get Let's Encrypt certificate
sudo certbot certonly --standalone -d mhealth.iitgn.ac.in --email your@email.com --agree-tos

# Renew Let's Encrypt certificate
sudo certbot renew

# Check certificate expiry
openssl x509 -in ssl/cert.pem -noout -enddate

# Test HTTPS
curl -k https://mhealth.iitgn.ac.in

# Restart frontend with new certificate
docker restart mhealth-frontend
```

---

## Summary

After completing this guide:

✅ HTTPS enabled on port 443
✅ HTTP (port 80) redirects to HTTPS
✅ SSL certificate configured
✅ Secure access: `https://mhealth.iitgn.ac.in`

**Recommended:** Use **Let's Encrypt** (Option 2) for production deployments with public domains.
**For Testing:** Use **Self-Signed** (Option 1) for internal/development environments.
