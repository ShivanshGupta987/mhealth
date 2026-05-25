# Dockerfile for ML Service
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create model store directory
RUN mkdir -p model_store

# Copy model files (if available)
# In production, these should be mounted as volumes or downloaded from object storage
COPY model_store/ ./model_store/

# Expose port
EXPOSE 8001

# Set environment variables
ENV ML_SERVICE_HOST=0.0.0.0
ENV ML_SERVICE_PORT=8001
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
