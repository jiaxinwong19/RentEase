import pika
import os
import time
import socket
import sys

# RabbitMQ connection details
rabbitmq_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")  # Default to container name
exchange_name = os.environ.get("EXCHANGE_NAME", "order_exchange")

# Print environment information
print(f"🔍 Environment variables:")
print(f"  - RABBITMQ_HOST: {os.environ.get('RABBITMQ_HOST', 'not set')}")
print(f"  - EXCHANGE_NAME: {os.environ.get('EXCHANGE_NAME', 'not set')}")
print(f"  - Using host: {rabbitmq_host}")
print(f"  - Using exchange: {exchange_name}")

# Queues and routing keys
queues = {
    "successful_transaction_shipping": "transaction.successful",
    "successful_transaction_inventory": "transaction.successful", 
    "unsuccessful_transaction_queue": "transaction.unsuccessful",
}

def check_host_connectivity(host, port=5672, timeout=2):
    """Check if we can connect to the host at the specified port"""
    try:
        socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_obj.settimeout(timeout)
        result = socket_obj.connect_ex((host, port))
        socket_obj.close()
        return result == 0
    except socket.error as e:
        print(f"Socket error when checking connectivity to {host}:{port}: {e}")
        return False

def setup_rabbitmq():
    """Setup RabbitMQ exchange and queues"""
    print(f"🔄 Attempting to connect to RabbitMQ at {rabbitmq_host}...")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()

    # Declare the exchange (topic allows routing based on keys)
    print(f"📢 Declaring exchange '{exchange_name}'...")
    channel.exchange_declare(exchange=exchange_name, exchange_type="topic", durable=True)

    # Declare and bind queues
    for queue_name, routing_key in queues.items():
        print(f"📋 Declaring queue '{queue_name}'...")
        channel.queue_declare(queue=queue_name, durable=True)
        
        print(f"🔗 Binding queue '{queue_name}' to exchange '{exchange_name}' with routing key '{routing_key}'...")
        channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
        
        print(f"✅ Queue '{queue_name}' successfully configured!")

    connection.close()
    print("🎉 RabbitMQ setup completed successfully!")

def setup_rabbitmq_with_retry(max_attempts=30, delay=5):
    """Try to set up RabbitMQ with retries"""
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        print(f"🔄 Attempt {attempts}/{max_attempts} to set up RabbitMQ...")
        
        # First check if we can even reach the host
        if not check_host_connectivity(rabbitmq_host):
            print(f"❌ Cannot connect to {rabbitmq_host}:5672. Host may be down or unreachable.")
            print(f"⏳ Waiting {delay} seconds before retry...")
            time.sleep(delay)
            continue
            
        try:
            setup_rabbitmq()
            print("✅ RabbitMQ setup completed successfully!")
            return True
        except pika.exceptions.AMQPConnectionError as e:
            print(f"❌ AMQP Connection Error: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error during setup: {str(e)}")
        
        print(f"⏳ Waiting {delay} seconds before retry...")
        time.sleep(delay)
    
    print("❌ Failed to set up RabbitMQ after maximum attempts.")
    return False

if __name__ == "__main__":
    print("===== Setting up RabbitMQ for Order System =====")
    
    # Try DNS lookup to check name resolution
    try:
        print(f"🔍 Attempting to resolve hostname '{rabbitmq_host}'...")
        ip_address = socket.gethostbyname(rabbitmq_host)
        print(f"✅ Hostname resolved to IP: {ip_address}")
    except socket.gaierror:
        print(f"❌ Cannot resolve hostname '{rabbitmq_host}'. Check network configuration.")
    
    # Run setup with retry
    success = setup_rabbitmq_with_retry()
    
    if success:
        print("===== RabbitMQ Setup Complete =====")
        sys.exit(0)
    else:
        print("===== RabbitMQ Setup Failed =====")
        sys.exit(1)