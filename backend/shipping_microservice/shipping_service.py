import os
import json
import shippo
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, jsonify, request
from datetime import datetime
from flask_cors import CORS
from dotenv import load_dotenv
import pika
import time
import threading
import logging
import sys

# Set up proper logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('shipping_service')
logger.info("============ SHIPPING SERVICE STARTING ============")

# Load API keys from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
# Update CORS configuration to allow credentials and specific origin
# shipping_service.py
from flask_cors import CORS

CORS(app, resources={
    r"/shipping/*": {
        "origins": ["http://localhost", "http://localhost:5173"],  # <- Allow both!
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})


# Configure Shippo with API key from environment
shippo_api_key = os.environ.get('SHIPPO_API_KEY')
if not shippo_api_key:
    logger.warning("SHIPPO_API_KEY not set in environment!")
shippo.config.api_key = shippo_api_key

# Carrier account from environment
CARRIER_ACCOUNT = os.environ.get('CARRIER_ACCOUNT')
SERVICE_LEVEL = 'usps_priority'  # Default service level

# Initialize Firebase
db = None
try:
    cred_path = os.environ.get('FIREBASE_CREDENTIALS')
    logger.info(f"Firebase credentials path: {cred_path}")
    
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        logger.info("Using Firebase certificate credentials")
    else:
        cred = credentials.ApplicationDefault()
        logger.info("Using Firebase application default credentials")
    
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Firebase: {e}")
    logger.warning("WARNING: Firebase initialization failed - using in-memory storage")

# In-memory storage as fallback if Firebase fails
in_memory_storage = {}

def save_to_firebase(order_id, shipping_data):
    """Save shipping data to Firebase"""
    try:
        if db:
            db.collection('shipping_labels').document(order_id).set(shipping_data)
            logger.info(f"Saved shipping data to Firebase for order {order_id}")
            return True
        else:
            # Fallback to in-memory storage
            in_memory_storage[order_id] = shipping_data
            logger.info(f"Saved shipping data to in-memory storage for order {order_id}")
            return True
    except Exception as e:
        logger.error(f"Error saving to Firebase: {e}")
        in_memory_storage[order_id] = shipping_data
        return False

def get_from_firebase(order_id):
    """Get shipping data from Firebase"""
    try:
        if db:
            doc_ref = db.collection('shipping_labels').document(order_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            else:
                logger.info(f"No shipping data found for order {order_id}")
                return None
        else:
            result = in_memory_storage.get(order_id)
            if not result:
                logger.info(f"No shipping data found in memory for order {order_id}")
            return result
    except Exception as e:
        logger.error(f"Error getting from Firebase: {e}")
        return in_memory_storage.get(order_id)

def create_shipping_label(order_data):
    try:
        logger.info(f"Creating shipping label for order {order_data['order_id']}...")
        
        # Check if we already have a label for this order
        existing_data = get_from_firebase(order_data['order_id'])
        if existing_data and 'label_url' in existing_data and existing_data['label_url']:
            logger.info(f"Label already exists for order {order_data['order_id']}")
            return existing_data
        
        # Use the sender address from the message or the default renter info
        sender_address = order_data.get("sender")
        if not sender_address:
            logger.error("Missing sender address in order data")
            return None
            
        recipient_address = order_data.get("recipient")
        if not recipient_address:
            logger.error("Missing recipient address in order data")
            return None
            
        parcel = order_data.get("parcel")
        if not parcel:
            logger.error("Missing parcel information in order data")
            return None
        
        # Log the request data for debugging
        logger.debug(f"Shipment request data:")
        logger.debug(f"From: {json.dumps(sender_address)}")
        logger.debug(f"To: {json.dumps(recipient_address)}")
        logger.debug(f"Parcel: {json.dumps(parcel)}")
        
        # Create shipment
        try:
            shipment = shippo.Shipment.create(
                address_from=sender_address,
                address_to=recipient_address,
                parcels=[parcel],
                async_=False
            )
            
            logger.debug("Shipment created successfully")
        except Exception as ship_error:
            logger.error(f"Error creating Shippo shipment: {str(ship_error)}")
            return None
        
        # Filter for USPS rates among all returned rates
        usps_rates = [rate for rate in shipment.rates if rate.provider.lower() == "usps"]
        if not usps_rates:
            logger.error("No USPS rates found for shipment")
            return None

        # Choose the first USPS rate
        rate = usps_rates[0]
        logger.info(f"Selected shipping rate: {rate.provider} - {rate.servicelevel.name} - {rate.amount}")
        
        # Create transaction to purchase the label
        try:
            transaction = shippo.Transaction.create(
                rate=rate.object_id,
                label_file_type="PDF",
                async_=False
            )
            logger.debug("Transaction created successfully")
        except Exception as trans_error:
            logger.error(f"Error creating Shippo transaction: {str(trans_error)}")
            return None
        
        # Keep trying until we get a SUCCESS status
        retry_count = 0
        current_transaction = transaction
        max_retries = 5  # Set a maximum retry limit
        
        while current_transaction.status != "SUCCESS" and retry_count < max_retries:
            if current_transaction.status == "QUEUED":
                retry_count += 1
                logger.info(f"Transaction is queued. Retrying... (attempt {retry_count}/{max_retries})")
                
                queued_info = {
                    "order_id": order_data["order_id"],
                    "status": "processing",
                    "transaction_id": current_transaction.object_id,
                    "created_at": datetime.now().isoformat(),
                    "retry_count": retry_count,
                    "renter_id": order_data.get("renter_id"),
                    "user_id": order_data.get("user_id")
                }
                save_to_firebase(order_data["order_id"], queued_info)
                
                time.sleep(5)
                try:
                    current_transaction = shippo.Transaction.retrieve(transaction.object_id)
                except Exception as retrieve_error:
                    logger.error(f"Error retrieving transaction: {str(retrieve_error)}")
                    break
            elif current_transaction.status in ["ERROR", "INVALID"]:
                logger.error(f"Transaction failed with status {current_transaction.status}: {current_transaction.messages}")
                return None
            else:
                logger.warning(f"Unknown transaction status: {current_transaction.status}")
                time.sleep(5)
                try:
                    current_transaction = shippo.Transaction.retrieve(transaction.object_id)
                except Exception as retrieve_error:
                    logger.error(f"Error retrieving transaction: {str(retrieve_error)}")
                    break
        
        if current_transaction.status != "SUCCESS":
            logger.error(f"Failed to get SUCCESS status after {retry_count} retries")
            return None
            
        logger.info(f"Transaction completed successfully after {retry_count} retries!")
        
        shipping_info = {
            "order_id": order_data["order_id"],
            "label_url": current_transaction.label_url,
            "tracking_number": current_transaction.tracking_number,
            "carrier": rate.provider,
            "service": rate.servicelevel.name,
            "created_at": datetime.now().isoformat(),
            "status": "label_created",
            "retry_count": retry_count,
            "renter_id": order_data.get("renter_id"),
            "user_id": order_data.get("user_id"),
            "product_id": order_data.get("product_id")
        }
        
        save_to_firebase(order_data["order_id"], shipping_info)
        return shipping_info
            
    except Exception as e:
        logger.error(f"Error creating label: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def process_message(message):
    """Process a message"""
    try:
        logger.info(f"Processing message for order {message.get('order_id')}...")
        
        # Validate message structure
        if not message.get('order_id'):
            logger.error("Missing order_id in message")
            return None
            
        shipping_info = create_shipping_label(message)
        if shipping_info:
            logger.info(f"Successfully processed order {message.get('order_id')}")
            return shipping_info
        else:
            logger.error(f"Failed to create shipping label for order {message.get('order_id')}")
            return None
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# --- RabbitMQ Integration ---
# Use the correct host depending on environment (container vs local)
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', "rabbitmq")
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
EXCHANGE_NAME = os.environ.get('EXCHANGE_NAME', "order_exchange")
QUEUE_NAME = "successful_transaction_shipping"  # New fixed queue name for Shipping
ROUTING_KEY = "transaction.successful"

logger.info(f"RabbitMQ Configuration:")
logger.info(f"  Host: {RABBITMQ_HOST}")
logger.info(f"  Port: {RABBITMQ_PORT}")
logger.info(f"  Exchange: {EXCHANGE_NAME}")
logger.info(f"  Queue: {QUEUE_NAME}")
logger.info(f"  Routing Key: {ROUTING_KEY}")

# Global connection and channel variables
rabbit_connection = None
rabbit_channel = None

def setup_rabbitmq():
    """Set up RabbitMQ connection and channel"""
    global rabbit_connection, rabbit_channel
    try:
        logger.info(f"Connecting to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}...")
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        rabbit_connection = pika.BlockingConnection(parameters)
        rabbit_channel = rabbit_connection.channel()
        
        # Declare exchange
        logger.info(f"Declaring exchange: {EXCHANGE_NAME}")
        rabbit_channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)
        
        # Declare queue
        logger.info(f"Declaring queue: {QUEUE_NAME}")
        queue_result = rabbit_channel.queue_declare(queue=QUEUE_NAME, durable=True)
        queue_message_count = queue_result.method.message_count
        logger.info(f"Queue has {queue_message_count} messages waiting")
        
        # Bind queue to exchange
        logger.info(f"Binding queue {QUEUE_NAME} to exchange {EXCHANGE_NAME} with routing key {ROUTING_KEY}")
        rabbit_channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=ROUTING_KEY)
        
        # Set prefetch count
        rabbit_channel.basic_qos(prefetch_count=1)
        logger.info("Connected to RabbitMQ successfully")
        return True
    except Exception as e:
        logger.error(f"Error connecting to RabbitMQ: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def callback(ch, method, properties, body):
    """Callback function for RabbitMQ consumer in shipping service"""
    logger.info("="*50)
    logger.info("CALLBACK TRIGGERED - MESSAGE RECEIVED")
    logger.info("="*50)
    
    try:
        logger.info(f"Message routing key: {method.routing_key}")
        logger.info(f"Message delivery tag: {method.delivery_tag}")
        logger.info(f"Message body type: {type(body)}")
        
        # Try to decode and parse the message
        try:
            message_str = body.decode('utf-8')
            logger.info(f"Received message: {message_str[:200]}...")  # Log first 200 chars only
            message = json.loads(message_str)
        except Exception as parse_error:
            logger.error(f"Error parsing message: {parse_error}")
            # Acknowledge the message to remove it from queue even if we can't process it
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        order_id = message.get("orderID")
        if not order_id:
            logger.error("Missing orderID in message")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        logger.info(f"Processing shipping for order: {order_id}")
        
        # Check for required fields
        required_fields = [
            "orderID", "userID", "productID", "productName", "productDesc", 
            "length", "width", "height", "weight", "distanceUnit", "massUnit",
            "userEmail", "recipientName", "recipientStreet", "recipientCity", 
            "recipientState", "recipientZip", "recipientCountry",
            "senderName", "senderStreet", "senderCity", "senderState", 
            "senderZip", "senderCountry", "senderEmail"
        ]
        
        # Log all fields found in the message for debugging
        message_fields = list(message.keys())
        logger.debug(f"Fields in message: {message_fields}")
        
        missing_fields = [field for field in required_fields if field not in message]
        if missing_fields:
            logger.error(f"Message missing required fields: {missing_fields}")
            # Acknowledge the message to remove it from queue
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Transform the message to shipping service format using data directly from the message
        transformed_message = {
            "order_id": message.get("orderID"),
            "sender": {
                "name": message.get("senderName"),
                "street1": message.get("senderStreet"),
                "city": message.get("senderCity"),
                "state": message.get("senderState"),
                "zip": str(message.get("senderZip")),
                "country": message.get("senderCountry"),
                "phone": message.get("senderPhone") or "+1 555 123 4567",
                "email": message.get("senderEmail")
            },
            "recipient": {
                "name": message.get("recipientName") or message.get("userEmail").split('@')[0],
                "street1": message.get("recipientStreet"),
                "city": message.get("recipientCity"),
                "state": message.get("recipientState"),
                "zip": str(message.get("recipientZip")),
                "country": message.get("recipientCountry") or "US",
                "phone": message.get("recipientPhone") or "+1 555 987 6543",
                "email": message.get("userEmail")
            },
            "parcel": {
                "length": str(message.get("length")),
                "width": str(message.get("width")),
                "height": str(message.get("height")),
                "distance_unit": message.get("distanceUnit"),
                "weight": str(message.get("weight")),
                "mass_unit": message.get("massUnit")
            },
            # Include other fields from message
            "transaction_id": message.get("transactionID"),
            "user_id": message.get("userID"),
            "renter_id": message.get("renterID"),
            "payment_amount": message.get("paymentAmount"),
            "product_id": message.get("productID"),
            "product_desc": message.get("productDesc")
        }
        
        logger.info(f"Transformed message for processing: {json.dumps(transformed_message)[:200]}...")
        
        result = process_message(transformed_message)
        if result:
            logger.info(f"Successfully processed shipping for order: {transformed_message['order_id']}")
        else:
            logger.error(f"Failed to process shipping for order: {transformed_message['order_id']}")
        
        # Acknowledge the message regardless of result to avoid redelivery loop
        logger.info(f"Acknowledging message with delivery tag: {method.delivery_tag}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error in consumer callback: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Always acknowledge to prevent message build-up
        # If we want to retry, we could set requeue=True, but that could create an infinite loop
        # for messages that always cause errors
        logger.info(f"Acknowledging message despite error to prevent queue build-up")
        ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consumer():
    """Start the RabbitMQ consumer"""
    global rabbit_channel
    if not setup_rabbitmq():
        logger.error("Could not set up RabbitMQ, consumer not started")
        return False
    
    try:
        # Set up the consumer
        logger.info(f"Setting up consumer for queue: {QUEUE_NAME}")
        rabbit_channel.basic_consume(
            queue=QUEUE_NAME,
            on_message_callback=callback,
            auto_ack=False  # Important: let the callback handle acknowledgments
        )
        logger.info(f"Consumer started, waiting for messages on queue: {QUEUE_NAME}")
        # Start consuming (this will block the thread)
        rabbit_channel.start_consuming()
    except Exception as e:
        logger.error(f"Error starting consumer: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def start_consumer_thread():
    """Start the consumer in a separate thread"""
    logger.info("Starting consumer thread...")
    consumer_thread = threading.Thread(target=start_consumer)
    consumer_thread.daemon = True  # Thread will exit when main thread exits
    consumer_thread.start()
    logger.info("Consumer thread started")
    return consumer_thread

# --- API Endpoints ---

@app.route('/shipping/<order_id>/label', methods=['GET'])
def get_label(order_id):
    """Get the shipping label URL for an order"""
    logger.info(f"Request for label URL for order: {order_id}")
    shipping_data = get_from_firebase(order_id)
    if shipping_data and 'label_url' in shipping_data:
        return jsonify({"label_url": shipping_data["label_url"]}), 200
    return jsonify({"error": "Shipping label not found"}), 404

@app.route('/shipping/<order_id>', methods=['GET'])
def get_shipping_info(order_id):
    """Get all shipping information for an order"""
    logger.info(f"Request for shipping info for order: {order_id}")
    shipping_data = get_from_firebase(order_id)
    if shipping_data:
        return jsonify(shipping_data), 200
    return jsonify({"error": "Shipping information not found"}), 404

@app.route('/shipping/process-custom', methods=['POST'])
def process_custom_message():
    """Process a custom message provided in the request body"""
    logger.info("Request to process custom message")
    if not request.json:
        logger.error("No JSON data provided in request")
        return jsonify({"error": "No JSON data provided"}), 400
    
    logger.info(f"Processing custom message: {json.dumps(request.json)[:200]}...")
    result = process_message(request.json)
    if result:
        logger.info("Successfully processed custom message")
        return jsonify(result), 200
    logger.error("Failed to process custom message")
    return jsonify({"error": "Failed to process custom message"}), 500

@app.route('/shipping/consumer/status', methods=['GET'])
def consumer_status():
    """Check consumer status"""
    logger.info("Request for consumer status")
    global rabbit_connection, rabbit_channel
    if rabbit_connection and rabbit_connection.is_open and rabbit_channel and rabbit_channel.is_open:
        logger.info("Consumer status: running")
        return jsonify({
            "status": "running",
            "connection": "open",
            "queue": QUEUE_NAME,
            "exchange": EXCHANGE_NAME,
            "routing_key": ROUTING_KEY
        }), 200
    else:
        connection_status = "closed" if not rabbit_connection or not rabbit_connection.is_open else "open"
        channel_status = "closed" if not rabbit_channel or not rabbit_channel.is_open else "open"
        logger.warning(f"Consumer status: not running (connection: {connection_status}, channel: {channel_status})")
        return jsonify({
            "status": "not running",
            "connection": connection_status,
            "channel": channel_status
        }), 503

@app.route('/shipping/consumer/restart', methods=['POST'])
def restart_consumer():
    """Restart the consumer"""
    logger.info("Request to restart consumer")
    global rabbit_connection, rabbit_channel
    try:
        # Close existing connections if open
        if rabbit_channel and rabbit_channel.is_open:
            logger.info("Stopping existing consumer...")
            rabbit_channel.stop_consuming()
        if rabbit_connection and rabbit_connection.is_open:
            logger.info("Closing existing connection...")
            rabbit_connection.close()
        
        # Start a new consumer thread
        logger.info("Starting new consumer thread...")
        consumer_thread = start_consumer_thread()
        logger.info("Consumer restarted successfully")
        return jsonify({"status": "Consumer restarted", "success": True}), 200
    except Exception as e:
        logger.error(f"Failed to restart consumer: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"status": "Failed to restart consumer", "error": str(e), "success": False}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("Health check request")
    global rabbit_connection, rabbit_channel
    rabbitmq_status = "connected" if rabbit_connection and rabbit_connection.is_open else "disconnected"
    consumer_running = rabbit_channel and rabbit_channel.is_open
    
    response = {
        "status": "ok", 
        "service": "shipping-service",
        "rabbitmq": rabbitmq_status,
        "consumer": "running" if consumer_running else "not running"
    }
    logger.info(f"Health check response: {response}")
    return jsonify(response), 200

if __name__ == '__main__':
    # Start the consumer thread
    consumer_thread = start_consumer_thread()
    
    port = int(os.environ.get('PORT', 5009))
    debug = os.environ.get('DEBUG', 'true').lower() == 'true'
    logger.info(f"Starting Flask app on port {port} with debug={debug}")
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)