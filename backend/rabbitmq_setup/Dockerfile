FROM python:3.9-slim

WORKDIR /app

# Install pika for RabbitMQ communication
RUN pip install pika

# Copy the setup script
COPY rabbitmq_setup.py .

# Run the setup script
CMD ["python", "rabbitmq_setup.py"]