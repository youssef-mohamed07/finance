#!/bin/bash

# Production deployment script for Finance Analyzer

set -e

echo "🚀 Starting Finance Analyzer deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found. Please create it from .env.example"
    exit 1
fi

# Check if required environment variables are set
source .env
if [ -z "$ASSEMBLYAI_API_KEY" ] || [ -z "$SECRET_KEY" ]; then
    echo "❌ Error: Required environment variables not set"
    echo "Please ensure ASSEMBLYAI_API_KEY and SECRET_KEY are set in .env"
    exit 1
fi

# Build production image
echo "🔨 Building production Docker image..."
docker build -f Dockerfile.prod -t finance-analyzer:latest .

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Start new containers
echo "🚀 Starting new containers..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for health check
echo "⏳ Waiting for application to be healthy..."
sleep 10

# Check health
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Application is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Health check failed after 30 attempts"
        docker-compose -f docker-compose.prod.yml logs finance-analyzer
        exit 1
    fi
    sleep 2
done

echo "🎉 Deployment completed successfully!"
echo "📊 Application is running at http://localhost:8000"
echo "📋 Check logs with: docker-compose -f docker-compose.prod.yml logs -f"