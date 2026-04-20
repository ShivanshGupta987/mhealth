import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
COSMOSDB_CONNECTION_STRING = os.getenv("COSMOSDB_CONNECTION_STRING")
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")
REDIS_URL = os.getenv("REDIS_URL")
APP_HOST = os.getenv("APP_HOST")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
EXOTEL_SID = os.getenv("EXOTEL_SID")
EXOTEL_API_KEY = os.getenv("EXOTEL_API_KEY")
EXOTEL_API_TOKEN = os.getenv("EXOTEL_API_TOKEN")
EXOTEL_PHONE_NUMBER = os.getenv('EXOTEL_PHONE_NUMBER')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
RABBITMQ_URL = os.getenv('RABBITMQ_URL')
POSTGRES_DB_URL=os.getenv('POSTGRES_DB_URL')
MODEL_ID = os.getenv('MODEL_ID')
RETRY_DELAY_MINUTES = os.getenv('RETRY_DELAY_MINUTES')
MAX_RETRIES = os.getenv('MAX_RETRIES')
MIN_RECORDING_DURATION_SECONDS = os.getenv('MIN_RECORDING_DURATION_SECONDS')
EXOTEL_WEBHOOK_TOKEN = os.getenv('EXOTEL_WEBHOOK_TOKEN')
EXOTEL_APP_ID = os.getenv('EXOTEL_APP_ID')
# Path to sentiment/emotion model file (e.g., backend/model_store/best_model.pt)
SENTIMENT_MODEL_PATH = os.getenv('SENTIMENT_MODEL_PATH')

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
