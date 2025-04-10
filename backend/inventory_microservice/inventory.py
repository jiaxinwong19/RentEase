from flask import Flask, request, jsonify, make_response
import firebase_admin
from firebase_admin import credentials, firestore
from flask_cors import CORS
import pika
import json
import time
import threading
import sys
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

app = Flask(__name__)

# Configure CORS - Allow all origins for development
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins in development
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False,
        "send_wildcard": True
    }
})

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

class InventoryService:
    def __init__(self):
        self.collection = db.collection("inventory-db")

    def get_all_products(self):
        """Fetch all products from the inventory."""
        try:
            product_ref = self.collection.stream()
            
            products = []
            for doc in product_ref:
                data = doc.to_dict()
                # data["id"] = doc.id  # Add document ID for reference
                products.append({
                    # "id": doc.id,
                    "productID": data.get("productID"),
                    "productName": data.get("productName"),
                    "productDesc": data.get("productDesc"),
                    "originalImageUrl": data.get("originalImageUrl"),
                    "conditionScore": data.get("conditionScore"),
                    "price": data.get("price"),
                    "availability": data.get("availability"),
                    "userID": data.get("userID"),
                    "itemPrice": data.get("itemPrice")
                })

            return products
        except Exception as e:
            logging.debug(f"Error fetching products: {str(e)}")
            return {"error": str(e)}
        
    def get_product_by_id(self, product_id):
        """Fetch a specific product by its productID."""
        try:
            product_ref = self.collection.where("productID", "==", product_id).limit(1).stream()
            
            for doc in product_ref:
                data = doc.to_dict()
                # data["id"] = doc.id
                return data
                
            return {"error": "Product not found."}
        except Exception as e:
            logging.debug(f"Error fetching product {product_id}: {str(e)}")
            return {"error": str(e)}
            
    def add_product(self, product_data):
        """Add a new product to the inventory."""
        try:
            # Validate required fields
            required_fields = ["productName", "price", "userID", "length", "width", "height", "weight", "distanceUnit", "massUnit", "conditionScore", "originalImageUrl", "productDesc", "itemPrice"]
            for field in required_fields:
                if field not in product_data:
                    return {"error": f"Missing required field: {field}"}
            
            # Set default values for optional fields
            if "availability" not in product_data:
                product_data["availability"] = True
            if "conditionScore" not in product_data:
                product_data["conditionScore"] = 100
                
            # Generate a new productID
            try:
                products = self.collection.order_by("productID", direction=firestore.Query.DESCENDING).limit(1).stream()
                highest_id = 0
                for doc in products:
                    highest_id = doc.to_dict().get("productID", 0)
                product_data["productID"] = highest_id + 1
            except:
                # Fallback to a timestamp-based ID if query fails
                import time
                product_data["productID"] = int(time.time())
            
            # Add the product to Firestore
            result = self.collection.add(product_data)
            
            return {
                "message": "Product added successfully.",
                "productID": product_data["productID"],
                "documentID": result[1].id
            }
            
        except Exception as e:
            logging.debug(f"Error adding product: {str(e)}")
            return {"error": str(e)}
    
    def remove_product(self, product_id):
        """Remove a product from the inventory (soft delete only)."""
        try:
            # Query the collection to find the product by product_id
            product_ref = self.collection.where("productID", "==", product_id).stream()
            
            for doc in product_ref:
                # Soft delete by setting availability to False
                doc.reference.update({"availability": False})
                return {"message": f"Product {product_id} removed from available inventory."}
            
            return {"error": "Product not found or unauthorized access."}
        except Exception as e:
            logging.debug(f"Error removing product: {str(e)}")
            return {"error": str(e)}


    
    def update_product(self, product_id, user_id, update_data):
        """Update product information."""
        try:
            # Protect certain fields from being updated
            protected_fields = ["productID", "userID"]
            for field in protected_fields:
                if field in update_data:
                    del update_data[field]
                    
            product_ref = self.collection.where("productID", "==", product_id).where("userID", "==", user_id).stream()
            
            for doc in product_ref:
                doc.reference.update(update_data)
                return {"message": f"Product {product_id} updated successfully."}
            
            return {"error": "Product not found or unauthorized access."}
        except Exception as e:
            logging.debug(f"Error updating product: {str(e)}")
            return {"error": str(e)}
        

class InventoryConsumer:
    def __init__(self, inventory_service):
        self.inventory_service = inventory_service
        # Use a distinct fixed queue name for Inventory service
        self.queue_name = "successful_transaction_inventory"
        self.routing_key = "transaction.successful"

        # Retry logic for connecting to RabbitMQ
        for attempt in range(10):
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host='rabbitmq')
                )
                break
            except pika.exceptions.AMQPConnectionError:
                logging.debug(f"Attempt {attempt + 1}: Waiting for RabbitMQ...")
                time.sleep(3)
        else:
            raise Exception("❌ Failed to connect to RabbitMQ after 10 attempts.")

        # *** Ensure this line is executed ***
        self.channel = self.connection.channel()

        # Declare the exchange (topic exchange)
        self.channel.exchange_declare(exchange='order_exchange', exchange_type='topic', durable=True)
        
        # Declare the distinct fixed queue and bind it with the routing key
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        self.channel.queue_bind(exchange='order_exchange', queue=self.queue_name, routing_key=self.routing_key)


    def callback(self, ch, method, properties, body):
        """Callback function when a message is received."""
        try:
            message = json.loads(body)
            product_id = message.get("productID")

            if not product_id:
                logging.debug("Invalid message: Missing productID")
                return

            # Fetch the product
            product = self.inventory_service.get_product_by_id(product_id)
            if "error" in product:
                logging.debug(f"Product {product_id} not found.")
                return

            # Update inventory: Set availability to False
            self.inventory_service.update_product(product_id, product.get("userID"), {"availability": False})

            logging.debug(f"Updated inventory for product {product_id}: availability set to False")

            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logging.debug(f"Error processing message: {e}")

    def start_consuming(self):
        """Start consuming messages from RabbitMQ."""
        logging.debug("Waiting for messages...")
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback)
        self.channel.start_consuming()

    def run(self):
        """Run the consumer in a separate thread."""
        consumer_thread = threading.Thread(target=self.start_consuming)
        consumer_thread.daemon = True  # Allows the thread to exit when the main program exits
        consumer_thread.start()

# Create Flask application
app = Flask(__name__)
inventory_service = InventoryService()
consumer = InventoryConsumer(inventory_service)

consumer.run()

# API endpoints
@app.route('/inventory/products', methods=['GET'])
def get_products():
    """Get all available products"""
    products = inventory_service.get_all_products()
    logging.debug(f"Products API Response: {products}")  # Debugging logging.debug statement
    response = make_response(jsonify(products))
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/inventory/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID"""
    return jsonify(inventory_service.get_product_by_id(product_id))

@app.route('/inventory/products', methods=['POST'])
def add_product():
    """Add a new product"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    product_data = request.get_json()
    result = inventory_service.add_product(product_data)
    
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201

@app.route('/inventory/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    update_data = request.get_json()
    
    # Extract user_id from request body or query parameters
    user_id = update_data.get('userID')
    if not user_id:
        user_id = request.args.get('userID')
        if not user_id:
            return jsonify({"error": "userID is required"}), 400
    
    # Remove userID from update_data if it exists
    if 'userID' in update_data:
        del update_data['userID']
    
    result = inventory_service.update_product(product_id, int(user_id), update_data)
    
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@app.route('/inventory/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product based on its productID"""

    result = inventory_service.remove_product(product_id)

    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# Run the application
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5020)