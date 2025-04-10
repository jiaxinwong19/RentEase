#!/bin/bash
# Script to set up and run the entire application

echo "=== Setting up RentEase Microservices with Kong Gateway ==="

# Check for Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Create nginx.conf for frontend if it doesn't exist
if [ ! -f "./frontend/nginx.conf" ]; then
    echo "Creating nginx.conf for frontend..."
    cp ./frontend-nginx-conf.conf ./frontend/nginx.conf
fi

# Copy API config to frontend if needed
mkdir -p ./frontend/src/api
cp ./api-config.js ./frontend/src/api/config.js

# Verify Firebase service account files exist
SERVICE_ACCOUNT_FILES=(
    "./backend/conditionchecking_microservice/serviceAccountKey.json"
    "./backend/inventory_microservice/serviceAccountKey.json"
    "./backend/order_records_microservice/credentials.json"
    "./backend/transaction_microservice/serviceAccountKey.json"
    "./backend/shipping_microservice/serviceAccountKey.json"
)

MISSING_FILES=false
for file in "${SERVICE_ACCOUNT_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "Warning: Missing service account file: $file"
        MISSING_FILES=true
    fi
done

if [ "$MISSING_FILES" = true ]; then
    echo ""
    echo "Some Firebase service account files are missing."
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup aborted. Please ensure all service account files are in place."
        exit 1
    fi
fi

# Build and start the services in proper order
echo "Starting Kong database first..."
docker compose up -d kong-database

echo "Waiting for Kong database to be ready..."
until docker compose exec kong-database pg_isready -U kong; do
  echo "Waiting for database..."
  sleep 5
done

echo "Running Kong migrations..."
docker compose up -d kong-migration
docker compose wait kong-migration

echo "Starting remaining services..."
docker compose up -d

echo "Waiting for Kong to be fully initialized..."
MAX_ATTEMPTS=60
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  if curl -s -I http://localhost:18001/ | grep "HTTP/1.1 200 OK" > /dev/null; then
    echo "Kong Admin API is available!"
    break
  fi
  ATTEMPT=$((ATTEMPT+1))
  echo "Waiting for Kong Admin API... Attempt $ATTEMPT of $MAX_ATTEMPTS"
  sleep 10
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
  echo "Warning: Failed to connect to Kong after $MAX_ATTEMPTS attempts."
  echo "Viewing Kong logs:"
  docker compose logs kong | tail -20
  
  read -p "Do you want to continue with setup anyway? (y/n): " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup aborted. Please check the logs and try again."
    exit 1
  fi
fi

# Configure Kong routes 
echo "Configuring Kong Gateway..."
chmod +x ./kong-setup.sh
./kong-setup.sh

echo "=== Setup Complete ==="
echo ""
echo "Services are now running:"
echo "- Frontend: http://localhost"
echo "- Kong Gateway: http://localhost:18000"
echo "- Kong Admin API: http://localhost:18001"
echo "- Kong Admin GUI: http://localhost:18002"
echo "- RabbitMQ Management: http://localhost:15672"
echo ""
echo "To shut down the services, run: docker compose down"