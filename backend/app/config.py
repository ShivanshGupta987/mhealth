import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")
APP_HOST = os.getenv("APP_HOST")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "180"))
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
MINIO_BUCKET = os.getenv('MINIO_BUCKET', CONTAINER_NAME or 'twilio-recordings')
RABBITMQ_URL = os.getenv('RABBITMQ_URL')
POSTGRES_DB_URL = os.getenv('POSTGRES_DB_URL')
MODEL_ID = os.getenv('MODEL_ID')
RETRY_DELAY_MINUTES = int(os.getenv('RETRY_DELAY_MINUTES', '5'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
MIN_RECORDING_DURATION_SECONDS = int(os.getenv('MIN_RECORDING_DURATION_SECONDS', '180'))
# ML Service Configuration (Microservice)
ML_SERVICE_URL = os.getenv('ML_SERVICE_URL', 'http://localhost:8001')
ML_SERVICE_TIMEOUT = int(os.getenv('ML_SERVICE_TIMEOUT', '30'))

# Email configuration for password reset
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', SMTP_USER)
SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'MHealth Platform')

# Frontend URL - supports comma-separated list, uses first for email links
_frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
FRONTEND_URL = _frontend_url.split(',')[0].strip() if _frontend_url else 'http://localhost:5173'

PASSWORD_RESET_TOKEN_EXPIRE_HOURS = int(os.getenv('PASSWORD_RESET_TOKEN_EXPIRE_HOURS', '2'))

# IITGN SSO (Keycloak / OpenID Connect)
IITGN_CLIENT_ID = os.getenv('IITGN_CLIENT_ID', '')
IITGN_CLIENT_SECRET = os.getenv('IITGN_CLIENT_SECRET', '')
# Must exactly match the redirect URI registered with IITGN IT
IITGN_REDIRECT_URI = os.getenv('IITGN_REDIRECT_URI', 'https://mhealth.iitgn.ac.in/api/auth/sso/callback')

# SSO email allowlist
# Format: comma-separated list of entries.
# Supported entry formats:
# - exact email: alice@iitgn.ac.in
# - domain pattern: @iitgn.ac.in
# Leave empty to allow all emails.
_raw_iitgn_allowed_emails = os.getenv('IITGN_ALLOWED_EMAILS', '')
IITGN_ALLOWED_EMAILS = [
	item.strip().lower()
	for item in _raw_iitgn_allowed_emails.split(',')
	if item.strip()
]
