#!/bin/bash

# SSL Setup Script using a local Certificate Authority (CA)
# ---------------------------------------------------------
# This creates:
#   ssl/ca.crt      — CA certificate (import this into browsers/OS once)
#   ssl/cert.pem    — Server certificate (used by nginx)
#   ssl/key.pem     — Server private key (used by nginx)
#
# After importing ssl/ca.crt into your browser/OS once,
# https://mhealth.iitgn.ac.in will show a green padlock with NO warning.
#
# Run on server: ./setup-ssl.sh

set -e

echo "========================================"
echo "mHealth SSL Setup - Local CA + Server Cert"
echo "========================================"
echo ""

# Check if running on server
if [ ! -d "/home/shivansh.gupta/mhealth" ]; then
    echo "⚠️  This script should be run on the server"
    echo "SSH to server first: ssh -p 2022 shivansh.gupta@10.0.62.206"
    exit 1
fi

cd /home/shivansh.gupta/mhealth/backend

# Create SSL directory
mkdir -p ssl
cd ssl

# Check if already set up
if [ -f "cert.pem" ] && [ -f "key.pem" ] && [ -f "ca.crt" ]; then
    echo "⚠️  SSL certificates already exist!"
    read -p "Do you want to replace them? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing certificates."
        exit 0
    fi
fi

DOMAIN="mhealth.iitgn.ac.in"
IP="10.0.62.206"
CA_SUBJ="/C=IN/ST=Gujarat/L=Gandhinagar/O=IIT Gandhinagar/OU=mHealth CA/CN=mHealth Local CA"
CERT_SUBJ="/C=IN/ST=Gujarat/L=Gandhinagar/O=IIT Gandhinagar/OU=mHealth/CN=${DOMAIN}"

# ── Step 1: Generate CA key and CA certificate (valid 10 years) ──────────────
echo ""
echo "[1/3] Generating Certificate Authority (CA)..."

openssl genrsa -out ca.key 4096 2>/dev/null

openssl req -x509 -new -nodes \
  -key ca.key \
  -sha256 \
  -days 3650 \
  -out ca.crt \
  -subj "${CA_SUBJ}" \
  2>/dev/null

echo "✅ CA created (valid 10 years)"

# ── Step 2: Generate server key and CSR ─────────────────────────────────────
echo ""
echo "[2/3] Generating server key and certificate..."

openssl genrsa -out key.pem 2048 2>/dev/null

openssl req -new \
  -key key.pem \
  -out server.csr \
  -subj "${CERT_SUBJ}" \
  2>/dev/null

# ── Step 3: Sign server cert with CA, including SANs ─────────────────────────
# Subject Alternative Names are required by modern browsers (Chrome, Firefox, Edge)
cat > san.ext <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=@alt_names

[alt_names]
DNS.1=${DOMAIN}
IP.1=${IP}
IP.2=127.0.0.1
EOF

openssl x509 -req \
  -in server.csr \
  -CA ca.crt \
  -CAkey ca.key \
  -CAcreateserial \
  -out cert.pem \
  -days 3650 \
  -sha256 \
  -extfile san.ext \
  2>/dev/null

# Clean up temporary files
rm -f server.csr san.ext ca.srl

echo "✅ Server certificate created (valid 10 years, signed by local CA)"

# ── Permissions ──────────────────────────────────────────────────────────────
chmod 600 ca.key key.pem
chmod 644 ca.crt cert.pem

echo ""
echo "Setting file permissions..."
echo "✅ Permissions set"

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "Generated Files:"
echo "========================================"
echo "  ssl/ca.crt   — CA certificate (IMPORT THIS into browsers/OS)"
echo "  ssl/cert.pem — Server certificate (used by nginx automatically)"
echo "  ssl/key.pem  — Server private key  (used by nginx automatically)"
echo ""
echo "========================================"
echo "Certificate Details:"
echo "========================================"
openssl x509 -in cert.pem -noout -subject -issuer -dates

echo ""
echo "========================================"
echo "Next Steps:"
echo "========================================"
echo ""
echo "1. Restart Docker services:"
echo "   cd /home/shivansh.gupta/mhealth"
echo "   docker compose down && docker compose up -d --build"
echo ""
echo "2. Copy ssl/ca.crt to each device that needs to access the app:"
echo "   scp -P 2022 shivansh.gupta@10.0.62.206:/home/shivansh.gupta/mhealth/backend/ssl/ca.crt ."
echo ""
echo "3. Import ca.crt into your browser/OS (one-time per device):"
echo ""
echo "   Windows:"
echo "     Double-click ca.crt → Install Certificate → Local Machine"
echo "     → 'Place all certificates in the following store'"
echo "     → Browse → Trusted Root Certification Authorities → Finish"
echo ""
echo "   macOS:"
echo "     Double-click ca.crt → Keychain: System → Add"
echo "     → Double-click the cert → Trust → 'Always Trust' → close"
echo ""
echo "   Linux (Chrome/Edge):"
echo "     Settings → Privacy → Security → Manage certificates"
echo "     → Authorities tab → Import → select ca.crt → Trust for websites"
echo ""
echo "   Linux (Firefox):"
echo "     Settings → Privacy & Security → View Certificates"
echo "     → Authorities tab → Import → select ca.crt → Trust for websites"
echo ""
echo "4. Visit https://${DOMAIN} — green padlock, no warning! 🔒"
echo ""
