# RentEase - Microservice-based Equipment Rental Platform

RentEase is a comprehensive equipment rental platform built with a microservices architecture, featuring a Vue.js frontend and multiple Python microservices orchestrated with Docker Compose and Kong API Gateway.

## 🚀 Features

- **Equipment Rental Management**: Browse, rent, and manage equipment from inventory
- **Order Processing**: Complete order lifecycle management
- **Damage Reporting**: Condition checking and damage reporting capabilities 
- **Notifications**: Real-time user notifications
- **Payment Processing**: Integrated transaction handling
- **Shipping Management**: Track and manage equipment shipping

## 🏗️ Architecture

RentEase follows a microservices architecture with the following components:

### Frontend
- Vue 3 + Vite application using Vue Router
- Tailwind CSS for styling with Flowbite components
- Firebase integration for authentication and storage

### Backend Microservices
- **Order Composite**: Orchestrates the order process across multiple services
- **Inventory**: Manages product details and availability
- **Order Records**: Stores and retrieves order information
- **Transaction**: Handles payment processing
- **Notification**: Sends notifications to users (⚠️ Uses external API with limited calls)
- **Shipping**: Manages delivery logistics
- **Condition Checking**: Validates equipment condition (⚠️ Uses external API with limited calls)
- **Report Damage**: Handles damage reporting workflows
- **Check Expiry**: Monitors rental expirations

### Infrastructure
- **Kong API Gateway**: Routes and manages API requests
- **RabbitMQ**: Message broker for asynchronous communication
- **Firebase/Firestore**: Document database for data storage
- **Docker & Docker Compose**: Container orchestration

## 🔧 Setup and Installation

### Prerequisites
- Docker and Docker Compose
- Firebase service account credentials

### Quick Start
1. Clone the repository:
   ```   git clone <repository-url>
   cd RentEase
   ```

2. Ensure all required Firebase service account files are in their respective directories:
   - `./backend/conditionchecking_microservice/serviceAccountKey.json`
   - `./backend/inventory_microservice/serviceAccountKey.json`
   - `./backend/order_records_microservice/credentials.json`
   - `./backend/transaction_microservice/serviceAccountKey.json`
   - `./backend/shipping_microservice/serviceAccountKey.json`

3. Run the setup script:
   ```
   chmod +x setup.sh
   bash setup.sh
   ```

4. Access the application:
   - Frontend: http://localhost
   - Kong Gateway: http://localhost:18000
   - Kong Admin API: http://localhost:18001
   - Kong Admin GUI: http://localhost:18002
   - RabbitMQ Management: http://localhost:15673

## 🖥️ Development

### Frontend Development
```
cd frontend
npm install
```

### Backend Development
Each microservice can be developed independently in its respective directory.

## 📦 Deployment

### ⚠️ IMPORTANT: Starting the Application

To start the entire application with all microservices, run this command:

```bash
docker compose up -d
```

This single command will start all containers and set up the complete environment.

## 🔌 API Configuration

Kong Gateway routes requests to appropriate microservices. The API configuration is handled by the `kong-setup.sh` script.

## 🧪 Technologies Used

- **Frontend**: Vue 3, Vite, Tailwind CSS, Flowbite
- **Backend**: Python, Flask
- **Database**: Firebase/Firestore
- **Messaging**: RabbitMQ
- **API Gateway**: Kong
- **Containerization**: Docker, Docker Compose

## 📝 License

[Your License Information]

## 👥 Contributors

[Your Team Information]