# Dockerfile for twilio_service
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Default: run the FastAPI API server
# Override CMD in docker-compose for worker / beat roles
CMD ["./start.sh", "api"]
