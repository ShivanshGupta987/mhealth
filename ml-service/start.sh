#!/bin/bash
# Quick start script for ML Service

set -e

echo "========================================="
echo "Mental Health ML Service - Quick Start"
echo "========================================="
echo ""

# Check if model file exists
if [ ! -f "model_store/best_model.pt" ]; then
    echo "ERROR: Model file not found!"
    echo "Please place best_model.pt in model_store/ directory"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the service
echo ""
echo "Starting ML Service on http://localhost:8001..."
echo "Press Ctrl+C to stop"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
