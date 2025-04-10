#!/bin/bash
# Kong Gateway Configuration Script

# Wait for Kong Admin API to be available
echo "Waiting for Kong Admin API to be available..."
while ! curl -s http://localhost:18001/ > /dev/null; do
  sleep 5
  echo "Still waiting for Kong..."
done
echo "Kong Admin API is available!"

# Delete all existing routes and services
echo "Deleting existing routes and services..."

# Get all routes and delete them
for route_id in $(curl -s http://localhost:18001/routes | grep -o '"id":"[^"]*' | cut -d'"' -f4); do
  echo "Deleting route: $route_id"
  curl -i -X DELETE http://localhost:18001/routes/$route_id
done

# Get all services and delete them
for service_id in $(curl -s http://localhost:18001/services | grep -o '"id":"[^"]*' | cut -d'"' -f4); do
  echo "Deleting service: $service_id"
  curl -i -X DELETE http://localhost:18001/services/$service_id
done

echo "Existing routes and services deleted!"

# Create a service for each microservice
echo "Creating services in Kong..."

# User Management Service (OutSystems)
curl -i -X POST http://localhost:18001/services \
  --data name=user-service \
  --data url=https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user

# Order Composite Service
curl -i -X POST http://localhost:18001/services \
  --data name=order-service \
  --data url=http://order-composite:5001/order_com

# Inventory Service
curl -i -X POST http://localhost:18001/services \
  --data name=inventory-service \
  --data url=http://inventory:5020/inventory

# Notification Service
curl -i -X POST http://localhost:18001/services \
  --data name=notification-service \
  --data url=http://notification:5010/notification

# Condition Check Service
curl -i -X POST http://localhost:18001/services \
  --data name=condition-service \
  --data url=http://condition-check:5005/condition



# Transaction Service
curl -i -X POST http://localhost:18001/services \
  --data name=transaction-service \
  --data url=http://transaction:5003/transaction

# Shipping Service
curl -i -X POST http://localhost:18001/services \
  --data name=shipping-service \
  --data url=http://shipping:5009/shipping

# Report Damage Service
curl -i -X POST http://localhost:18001/services \
  --data name=report-damage-service \
  --data url=http://report-damage:5004

echo "Services created successfully!"

# Create routes for each service
echo "Creating routes in Kong..."

# Order Service Routes - Main path
curl -i -X POST http://localhost:18001/services/order-service/routes \
  --data name=order-route \
  --data paths[]=/order

# Order Service - Create order endpoint
curl -i -X POST http://localhost:18001/services/order-service/routes \
  --data name=create-order-route \
  --data paths[]=/order_com/orders \
  --data methods[]=POST

# Order Service - Confirm order endpoint
curl -i -X POST http://localhost:18001/services/order-service/routes \
  --data name=confirm-order-route \
  --data paths[]=/order_com/confirm \
  --data strip_path=false \
  --data methods[]=POST

# Order Service - Notify shipping endpoint
curl -i -X POST http://localhost:18001/services/order-service/routes \
  --data name=notify-shipping-route \
  --data paths[]=/order_com/notify-shipping \
  --data strip_path=false \
  --data methods[]=POST

# User Service Routes (OutSystems)
# Add User endpoint
curl -i -X POST http://localhost:18001/services/user-service/routes \
  --data name=add-user-route \
  --data paths[]=/api/users/add \
  --data methods[]=POST \
  --data strip_path=true

# Get User Info endpoint
curl -i -X POST http://localhost:18001/services/user-service/routes \
  --data name=get-user-info-route \
  --data paths[]=/api/users/info \
  --data methods[]=GET \
  --data strip_path=true

# Get User Score endpoint
curl -i -X POST http://localhost:18001/services/user-service/routes \
  --data name=get-user-score-route \
  --data paths[]=/api/users/score \
  --data methods[]=GET \
  --data strip_path=true

# Get User Email endpoint
curl -i -X POST http://localhost:18001/services/user-service/routes \
  --data name=get-user-email-route \
  --data paths[]=/api/users/email \
  --data methods[]=GET \
  --data strip_path=true

# User Login endpoint
curl -i -X POST http://localhost:18001/services/user-service/routes \
  --data name=user-login-route \
  --data paths[]=/api/users/login \
  --data methods[]=POST \
  --data strip_path=true

# Inventory Service Routes
curl -i -X POST http://localhost:18001/services/inventory-service/routes \
  --data name=inventory-route \
  --data paths[]=/inventory

# Notification Service Routes
curl -i -X POST http://localhost:18001/services/notification-service/routes \
  --data name=notification-route \
  --data paths[]=/notification

# Condition Check Service Routes
curl -i -X POST http://localhost:18001/services/condition-service/routes \
  --data name=condition-route \
  --data paths[]=/condition


# Order Records Service
curl -i -X POST http://localhost:18001/services \
  --data name=order-records-service \
  --data url=http://order-records:5000/orders


# Order Records Service Routes
curl -i -X POST http://localhost:18001/services/order-records-service/routes \
  --data name=order-records-route \
  --data paths[]=/orders

curl -i -X POST http://localhost:18001/services \
  --data name=order-records-graphql-service \
  --data url=http://order-records:5000/graphql

# Add GraphQL endpoint for Order Records Service
curl -i -X POST http://localhost:18001/services/order-records-graphql-service/routes \
  --data name=graphql-route \
  --data paths[]=/graphql \
  --data methods[]=POST
  

# Transaction Service Routes
curl -i -X POST http://localhost:18001/services/transaction-service/routes \
  --data name=transaction-route \
  --data paths[]=/transaction

# Shipping Service Routes
curl -i -X POST http://localhost:18001/services/shipping-service/routes \
  --data name=shipping-route \
  --data paths[]=/shipping

# Report Damage Service Routes
curl -i -X POST http://localhost:18001/services/report-damage-service/routes \
  --data name=report-damage-route \
  --data paths[]=/report-damage \
  --data strip_path=false
  

echo "Routes created successfully!"
# Get the plugin ID
PLUGIN_ID=$(curl -s http://localhost:18001/plugins | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

# Delete the plugin
curl -i -X DELETE http://localhost:18001/plugins/$PLUGIN_ID
# Add CORS plugin globally (using JSON to avoid method schema error)
echo "Adding CORS plugin..."
CORS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:18001/plugins \
  -H "Content-Type: application/json" \
  -d '{
   "name": "cors",
    "config": {
    "origins": ["*"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    "headers": ["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With", "X-CSRF-Token"],
    "exposed_headers": ["Content-Type"],
    "credentials": true,
    "max_age": 3600
    }
  }'
  
  )

if [ "$CORS_RESPONSE" -eq 201 ]; then
  echo "✅ CORS plugin added successfully!"
else
  echo "❌ Failed to add CORS plugin. Status code: $CORS_RESPONSE"
fi

echo "Kong Gateway has been configured successfully!"