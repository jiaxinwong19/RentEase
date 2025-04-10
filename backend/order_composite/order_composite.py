import os
from flask import Flask, request, jsonify
import requests
import uuid
import json
import pika
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from local.env if present.
load_dotenv("local.env")

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",  # or specify http://localhost:5173 if using Vite
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin"],
        "supports_credentials": True
    }
})

# CORS(app, resources={
#     r"/*": {
#         "origins": "*",  # Allow all origins in development
#         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS","PATCH"],
#         "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin"],
#         "expose_headers": ["Content-Type"],
#         "supports_credentials": False,
#         "send_wildcard": True
#     }
# })

# Service endpoints loaded from environment variables with defaults.
ORDER_RECORDS_URL = os.environ.get("ORDER_RECORDS_URL", "http://localhost:5000/orders")
ORDER_RECORDS_URL_GRAPHQL = os.environ.get("ORDER_RECORDS_URL_GRAPHQL", "http://localhost:5000/graphql")
PRODUCT_DETAILS_URL = os.environ.get("PRODUCT_DETAILS_URL", "http://localhost:5020/inventory/products/")
NOTIFICATION_URL = os.environ.get("NOTIFICATION_URL", "http://localhost:5010/notification/renter/notify")
USER_EMAIL_URL = os.environ.get("USER_EMAIL_URL", "https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getEmail/")
TRANSACTION_SERVICE_URL = os.environ.get("TRANSACTION_SERVICE_URL", "http://localhost:5003")
SHIPPING_SERVICE_URL = os.environ.get("SHIPPING_SERVICE_URL", "http://localhost:5009")
USER_INFO_URL = os.environ.get("USER_INFO_URL", "https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getUserInfo")
STRIPE_CUSTOMER_URL = os.environ.get("STRIPE_CUSTOMER_URL", "https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getStripeCusID/")

# RabbitMQ connection details
rabbitmq_host = os.environ.get("RABBITMQ_HOST", "localhost")
exchange_name = os.environ.get("EXCHANGE_NAME", "order_exchange")

@app.route('/order_com/orders', methods=['POST'])
def create_order():
    # Step 1: Get request data
    data = request.json
    print(f"📝 Received order request data for product: {data.get('productId')}")
    
    # Basic validation: PRICE IS FROM UI AFTER CALCULATION OF DAYS*PER DAY CHARGE
    required_fields = ['price', 'productId', 'renterID', 'startDate', 'endDate', 'userID']
    if not all(k in data for k in required_fields):
        missing_fields = [field for field in required_fields if field not in data]
        print(f"❌ Missing required fields: {missing_fields}")
        return jsonify({"error": "Missing required fields", "missing": missing_fields}), 400
    
    # Generate random orderID
    order_id = str(uuid.uuid4())
    print(f"📌 Generated order ID: {order_id}")
    
    # Create order response payload
    order_response = {
        "orderID": order_id,
        "paymentAmount": data["price"],
        "productID": data["productId"],
        "renterID": data["renterID"],
        "startDate": data["startDate"],
        "endDate": data["endDate"],
        "status": "pending",
        "userID": data["userID"],
    }
    
    # Step 2: Post order to Order Records microservice 
    try:
        print(f"📤 Posting order #{order_id} to Order Records at {ORDER_RECORDS_URL}")
        print(f"🔍 Order data being sent: {order_response}")
        
        records_response = requests.post(ORDER_RECORDS_URL, json=order_response)
        
        print(f"📥 Response status code: {records_response.status_code}")
        print(f"📥 Response headers: {dict(records_response.headers)}")
        print(f"📥 Full response text: {records_response.text}")
        
        if records_response.status_code == 201:
            print(f"✅ Order Records: Added order #{order_id} successfully")
            response_data = records_response.json()
            print(f"✅ Response data: {response_data}")
        else:
            print(f"❌ Order Records failed: Status {records_response.status_code}")
            print(f"❌ Error response: {records_response.text}")
            try:
                error_json = records_response.json()
                print(f"❌ Parsed error details: {error_json}")
            except:
                print("❌ Could not parse error response as JSON")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: Could not connect to Order Records service")
        print(f"❌ Error details: {str(e)}")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout error: Order Records service took too long to respond")
        print(f"❌ Error details: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error when calling Order Records service")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Error details: {str(e)}")

    # Step 3: Get product details
    try:
        print(f"🔍 Getting details for product #{data['productId']}")
        product_response = requests.get(f"{PRODUCT_DETAILS_URL}{data['productId']}")
        product_data = product_response.json()
        product_desc = product_data.get("productDesc", "")
        original_image = product_data.get("originalImageUrl", "")
        if product_response.status_code == 200:
            print(f"✅ Product service: Retrieved details for product #{data['productId']}")
        else:
            print(f"❌ Product service failed: Status {product_response.status_code}")
    except Exception as e:
        print(f"❌ Product service connection error: {str(e)[:100]}")
        product_desc = ""
        original_image = ""
        
    # Step 3.5: Get user email
    user_email = ""
    try:
        print(f"👤 Getting email for user #{data['renterID']}")
        user_response = requests.get(f"{USER_EMAIL_URL}?id={data['renterID']}")
        if user_response.status_code == 200:
            user_data = user_response.json()
            user_email = user_data.get("email", "")
            print(f"✅ User service: Retrieved email for user #{data['renterID']}, email:{user_email}")
        else:
            print(f"❌ User service failed: Status {user_response.status_code} - {user_response.text[:100]}")
    except Exception as e:
        print(f"❌ User service connection error: {str(e)[:100]}")
        
    # Step 4: Send notification to renter
    notification_data = {
        "renterEmail": user_email,
        "productID": data.get("productId"),
        "prodDesc": product_desc,
        "originalImage": original_image,
        "orderID": order_id  # Include orderID here
    }
    print(notification_data)
    try:
        print(f"📧 Sending notification for order #{order_id}")
        notification_response = requests.post(
            NOTIFICATION_URL, 
            json=notification_data
        )
        if notification_response.status_code in [200, 201]:
            print(f"✅ Notification sent successfully for order #{order_id}")
        else:
            print(f"❌ Notification failed: Status {notification_response.status_code} - {notification_response.text[:100]}")
    except Exception as e:
        print(f"❌ Notification service connection error: {str(e)[:100]}")
    
    # Return the order response to the client
    print(f"✅ Order #{order_id} created successfully")
    return jsonify(order_response), 201


def publish_to_rabbitmq(transaction_status, message_data, order_id, user_id, product_id):
    """
    Publish comprehensive message data to RabbitMQ with all required fields.
    
    Args:
        transaction_status: Either "successful" or "unsuccessful"
        message_data: Base transaction details
        order_id: Order ID for the transaction
        user_id: User ID for the transaction (user who is renting the item)
        product_id: Product ID for the transaction
    """
    print(f"🔄 Attempting to publish message to RabbitMQ for order {order_id}")
    print(f"🔄 RabbitMQ host: {rabbitmq_host}, Exchange: {exchange_name}")
    print(f"🔄 Transaction status: {transaction_status}")
    
    try:
        # Get product details
        product_data = {}
        try:
            print(f"🔍 Getting product details from {PRODUCT_DETAILS_URL}{product_id}")
            product_response = requests.get(f"{PRODUCT_DETAILS_URL}{product_id}")
            print(f"🔍 Product API response status: {product_response.status_code}")
            
            if product_response.status_code == 200:
                product_data = product_response.json()
                print(f"✅ Retrieved product details for message data")
            else:
                print(f"❌ Failed to get product details: Status {product_response.status_code}")
                print(f"❌ Response text: {product_response.text[:100]}")
                return False
        except Exception as e:
            print(f"❌ Error getting product details: {str(e)}")
            return False

        # Get renter (owner) details - the person who owns the item
        renter_id = product_data.get("userID")
        if not renter_id:
            print(f"❌ No renter ID found in product data")
            print(f"❌ Product data: {product_data}")
            return False
            
        renter_details = {}
        try:
            print(f"🔍 Getting renter details from {USER_INFO_URL}?id={renter_id}")
            renter_info_response = requests.get(f"{USER_INFO_URL}?id={renter_id}")
            print(f"🔍 Renter API response status: {renter_info_response.status_code}")
            
            if renter_info_response.status_code == 200:
                renter_data = renter_info_response.json()
                renter_details = renter_data.get("details", {})
                print(f"✅ Retrieved renter details for message data")
            else:
                print(f"❌ Failed to get renter details: Status {renter_info_response.status_code}")
                print(f"❌ Response text: {renter_info_response.text[:100]}")
                return False
        except Exception as e:
            print(f"❌ Error getting renter details: {str(e)}")
            return False

        # Get user (recipient) details - the person renting the item
        user_details = {}
        try:
            print(f"🔍 Getting user details from {USER_INFO_URL}?id={user_id}")
            user_info_response = requests.get(f"{USER_INFO_URL}?id={user_id}")
            print(f"🔍 User API response status: {user_info_response.status_code}")
            
            if user_info_response.status_code == 200:
                user_data = user_info_response.json()
                user_details = user_data.get("details", {})
                print(f"✅ Retrieved user details for message data")
            else:
                print(f"❌ Failed to get user details: Status {user_info_response.status_code}")
                print(f"❌ Response text: {user_info_response.text[:100]}")
                return False
        except Exception as e:
            print(f"❌ Error getting user details: {str(e)}")
            return False

        # Assemble complete message with all required fields
        complete_message = {
            # Core order data from message_data
            "orderID": order_id,
            "userID": user_id,
            "productID": product_id,
            "status": message_data.get("status"),
            "paymentAmount": message_data.get("paymentAmount"),
            "stripeCusID": message_data.get("stripeCusID"),
            
            # Add transaction ID if available
            "transactionID": message_data.get("transactionID", ""),
            
            # Add error message if present
            "error": message_data.get("error", ""),
            
            # Product details from product_data
            "productName": product_data.get("productName", ""),
            "productDesc": product_data.get("productDesc", ""),
            "originalImage": product_data.get("originalImageUrl", ""),
            "price": product_data.get("price", 0),
            
            # Product shipping details
            "length": product_data.get("length", 0),
            "width": product_data.get("width", 0),
            "height": product_data.get("height", 0),
            "weight": product_data.get("weight", 0),
            "distanceUnit": product_data.get("distanceUnit", "in"),
            "massUnit": product_data.get("massUnit", "lb"),
            
            # User (recipient) email and details
            "userEmail": user_details.get("email", ""),
            "recipientName": user_details.get("name", ""),
            "recipientStreet": user_details.get("street1", ""),
            "recipientCity": user_details.get("city", ""),
            "recipientState": user_details.get("state", ""),
            "recipientZip": user_details.get("zip", ""),
            "recipientCountry": user_details.get("country", ""),
            "recipientPhone": user_details.get("phoneNo", ""),
            
            # Renter (sender) details - the person who owns the item
            "renterID": renter_id,
            "senderName": renter_details.get("name", ""),
            "senderStreet": renter_details.get("street1", ""),
            "senderCity": renter_details.get("city", ""),
            "senderState": renter_details.get("state", ""),
            "senderZip": renter_details.get("zip", ""),
            "senderCountry": renter_details.get("country", ""),
            "senderPhone": renter_details.get("phoneNo", ""),
            "senderEmail": renter_details.get("email", ""),
            
            
        }

        # DEBUG CODE 
        print("=="*40)
        print("DEBUG MESSAGE DATA CHECK:")
        required_fields = [
            "orderID", "userID", "productID", "productName", "productDesc", 
            "length", "width", "height", "weight", "distanceUnit", "massUnit",
            "userEmail", "recipientName", "recipientStreet", "recipientCity", 
            "recipientState", "recipientZip", "recipientCountry",
            "senderName", "senderStreet", "senderCity", "senderState", 
            "senderZip", "senderCountry", "senderEmail"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in complete_message or not complete_message.get(field):
                missing_fields.append(field)
                print(f"❌ MISSING REQUIRED FIELD: {field}")
            else:
                print(f"✅ Field {field} = {complete_message.get(field)}")
        
        if missing_fields:
            print(f"❌ TOTAL MISSING FIELDS: {len(missing_fields)} - {missing_fields}")
        else:
            print("✅ ALL REQUIRED FIELDS PRESENT")
        
        print("=="*40)
        #DEBUG END
        
        # Connect to RabbitMQ with more detailed error reporting
        try:
            print(f"🔌 Connecting to RabbitMQ at host: {rabbitmq_host}")
            connection_params = pika.ConnectionParameters(
                host=rabbitmq_host,
                connection_attempts=3,
                retry_delay=1,
                socket_timeout=5
            )
            connection = pika.BlockingConnection(connection_params)
            print(f"✅ Connected to RabbitMQ")
            
            channel = connection.channel()
            print(f"✅ Channel created")
            
            # Verify exchange exists (or create it)
            channel.exchange_declare(
                exchange=exchange_name, 
                exchange_type='topic',
                durable=True
            )
            print(f"✅ Exchange '{exchange_name}' verified/created")
            
            # Define the routing key based on status
            routing_key = f"transaction.{transaction_status}"
            print(f"📤 Publishing message with routing key: {routing_key}")

            # Enable publisher confirms
            channel.confirm_delivery()
            print(f"✅ Publisher confirms enabled")
            
            # Publish the message with more logging
            try:
                print(f"📤 Attempting to publish message...")
                was_published = channel.basic_publish(
                    exchange=exchange_name,
                    routing_key=routing_key,
                    body=json.dumps(complete_message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # make message persistent
                        content_type='application/json'
                    )
                )
                
                if was_published:
                    print(f"✅ Message for order #{order_id} CONFIRMED delivered to RabbitMQ")
                else:
                    print(f"❌ Message for order #{order_id} FAILED to deliver to RabbitMQ")
                    
                # Close connection properly
                connection.close()
                print(f"✅ RabbitMQ connection closed")
                
                return was_published
                
            except pika.exceptions.UnroutableError:
                print(f"❌ Message for order #{order_id} was returned as unroutable")
                print(f"❌ This usually means there are no bindings matching routing key '{routing_key}'")
                connection.close()
                return False
                
        except pika.exceptions.AMQPConnectionError as conn_error:
            print(f"❌ AMQP Connection Error: {str(conn_error)}")
            print("❌ Check that RabbitMQ service is running and accessible")
            return False
            
        except pika.exceptions.ChannelError as channel_error:
            print(f"❌ Channel Error: {str(channel_error)}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to publish RabbitMQ message: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


@app.route('/order_com/confirm/<string:order_id>', methods=['POST'])
def confirm_order(order_id):
    """
    Endpoint for renters to confirm pending orders.
    """
    print(f"📝 Processing confirmation for order #{order_id}")
    
    try:        
        # Update order status to accepted 
        try:
            update_data = {"status": "accepted"}
            order_url = f"{ORDER_RECORDS_URL}/{order_id}"
            print(f"🔄 Updating order #{order_id} status to 'accepted'")
            #Update order status in order records
            update_response = requests.patch(order_url, json=update_data)
            
            if update_response.status_code == 404:
                print(f"❌ Order #{order_id} not found")
                return jsonify({"error": "Order not found"}), 404
            elif update_response.status_code != 200:
                error_msg = f"Status {update_response.status_code} - {update_response.text[:100]}"
                print(f"❌ Update order status failed: {error_msg}")
                return jsonify({"error": error_msg}), 500
            else:
                print(f"✅ Updated order #{order_id} status to 'accepted'")
                
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"❌ Order Records connection error: {error_msg}")
            return jsonify({"error": f"Order Records connection error: {error_msg}"}), 500
    
        # Retrieve the updated order details
        try:
            print(f"🔍 Retrieving updated details for order #{order_id}")
            query = """
            query GetOrder($orderID: String!) {
                order(orderID: $orderID) {
                    orderID
                    paymentAmount
                    dailyPayment
                    productID
                    renterID
                    startDate
                    endDate
                    status
                    userID
                }
            }
            """            
            variables = {"orderID": order_id}
            graphql_payload = {"query": query, "variables": variables}
            #retrive order details 
            order_response = requests.post(ORDER_RECORDS_URL_GRAPHQL, json=graphql_payload)
            
            if order_response.status_code != 200:
                error_msg = f"Status {order_response.status_code} - {order_response.text[:100]}"
                print(f"❌ GraphQL query failed: {error_msg}")
                return jsonify({"error": error_msg}), 500
            
            response_data = order_response.json()
            if "errors" in response_data:
                error_msg = f"GraphQL errors: {str(response_data['errors'])[:100]}"
                print(f"❌ {error_msg}")
                return jsonify({"error": error_msg}), 500
            
            order_data = response_data['data']['order']
            user_id = order_data.get("userID")
            product_id = order_data.get("productID")
            payment_amount = order_data.get("paymentAmount")
            
            print(f"✅ Retrieved order details: ID #{order_id}, User #{user_id}, Product #{product_id}, Amount ${payment_amount}")

        except Exception as e:
            error_msg = str(e)[:100]
            print(f"❌ GraphQL query error: {error_msg}")
            return jsonify({"error": f"Error connecting to Order Records service: {error_msg}"}), 500        

        # Process the transaction with the userID
        try:
            # Prepare data for transaction endpoint
            transaction_data = {
                "orderID": order_id,
                "userID": user_id,
                "paymentAmt": payment_amount,  # Renamed from paymentAmount to paymentAmt
            }
            
            print(f"💰 Processing payment of ${payment_amount} for order #{order_id}")
            
            # Send data to transaction endpoint
            transaction_response = requests.post(
                f"{TRANSACTION_SERVICE_URL}/transaction/purchase",
                json=transaction_data
            )
            
            # Prepare base message data
            base_message_data = {
                "orderID": order_id,
                "userID": user_id,
                "paymentAmount": payment_amount,
                "status": "accepted"
            }
            
            if transaction_response.status_code not in [200, 201]:
                error_msg = f"Status {transaction_response.status_code} - {transaction_response.text[:100]}"
                print(f"❌ Transaction processing failed: {error_msg}")
                
                # Add error information to message data
                base_message_data["error"] = error_msg
                base_message_data["status"] = "payment_failed"
                
                # Update order status to payment_failed
                try:
                    update_data = {"status": "payment_failed"}
                    requests.patch(f"{ORDER_RECORDS_URL}/{order_id}", json=update_data)
                    print(f"✅ Updated order #{order_id} status to 'payment_failed'")
                except Exception as e:
                    print(f"❌ Failed to update order status: {str(e)[:100]}")
                
                # Publish unsuccessful transaction event with complete data
                publish_to_rabbitmq("unsuccessful", base_message_data, order_id, user_id, product_id)
                
                return jsonify({"error": f"Failed to process transaction: {error_msg}"}), 500
                    
            # Transaction was successful
            transaction_result = transaction_response.json()
            print(f"✅ Payment processed successfully for order #{order_id}")
            
            # Add transaction ID to message data
            base_message_data["transactionID"] = transaction_result.get("transactionID")
            
            # Update order status to paid
            try:
                update_data = {"status": "paid"}
                requests.patch(f"{ORDER_RECORDS_URL}/{order_id}", json=update_data)
                print(f"✅ Updated order #{order_id} status to 'paid'")
            except Exception as e:
                print(f"❌ Failed to update order status: {str(e)[:100]}")
            
            # Publish successful transaction event with complete data
            publish_to_rabbitmq("successful", base_message_data, order_id, user_id, product_id)
            
            # Return success response with transaction details
            return jsonify({
                "message": "Order confirmed and payment processed successfully",
                "orderID": order_id,
                "userID": user_id,
                "paymentAmount": payment_amount,
                "status": "accepted",
                "transactionResult": transaction_result
            }), 200
            
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"❌ Transaction service connection error: {error_msg}")
            
            # Create error message data
            error_message_data = {
                "orderID": order_id,
                "userID": user_id,
                "paymentAmount": payment_amount,
                "error": error_msg,
                "status": "error"
            }
            
            # Publish unsuccessful transaction event with complete data
            publish_to_rabbitmq("unsuccessful", error_message_data, order_id, user_id, product_id)
            
            return jsonify({"error": f"Error processing transaction: {error_msg}"}), 500
            
    except Exception as e:
        error_msg = str(e)[:100]
        print(f"❌ General confirm order error: {error_msg}")
        return jsonify({"error": f"Error confirming order: {error_msg}"}), 500
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/order_com/notify-shipping/<string:order_id>', methods=['POST'])
def notify_shipping_details(order_id):
    """Send shipping notifications to both user and renter"""
    logger.info(f"Processing shipping notification for order #{order_id}")
    
    try:
        # Log notification URL
        logger.info(f"NOTIFICATION_URL: {NOTIFICATION_URL}")
        
        # Step 1: Get shipping information
        shipping_url = f"{SHIPPING_SERVICE_URL}/shipping/{order_id}"
        logger.info(f"Calling shipping service at: {shipping_url}")
        shipping_response = requests.get(shipping_url)
        logger.info(f"Shipping response status: {shipping_response.status_code}")
        
        if shipping_response.status_code != 200:
            logger.error(f"Failed to get shipping data: {shipping_response.status_code}")
            return jsonify({"error": "Failed to retrieve shipping data"}), 500
            
        shipping_data = shipping_response.json()
        tracking_number = shipping_data.get("tracking_number")
        carrier = shipping_data.get("carrier", "USPS")
        user_id = shipping_data.get("user_id")
        renter_id = shipping_data.get("renter_id")
        product_id = shipping_data.get("product_id")

        logger.info(f"Shipping data received for order {order_id}:")
        logger.info(json.dumps(shipping_data, indent=2))
        
        required_fields = ["tracking_number", "user_id", "renter_id", "product_id"]
        missing_fields = [field for field in required_fields if not shipping_data.get(field)]
        logger.info(f"Missing required shipping fields: {missing_fields}")
        
        if not all([tracking_number, user_id, renter_id, product_id]):
            logger.error(f"Shipping data incomplete")
            return jsonify({"error": "Incomplete shipping data"}), 400
            
        # Step 2: Get product details
        product_url = f"{PRODUCT_DETAILS_URL}{product_id}"
        logger.info(f"Calling product service at: {product_url}")
        product_response = requests.get(product_url)
        logger.info(f"Product response status: {product_response.status_code}")
        
        if product_response.status_code != 200:
            logger.error(f"Failed to get product details: {product_response.status_code}")
            return jsonify({"error": "Failed to retrieve product details"}), 500
            
        product_data = product_response.json()
        product_name = product_data.get("productName", "")
        product_desc = product_data.get("productDesc", "")
        
        # Step 3: Get user details
        user_url = f"{USER_INFO_URL}?id={user_id}"
        logger.info(f"Calling user service at: {user_url}")
        user_response = requests.get(user_url)
        logger.info(f"User response status: {user_response.status_code}")
        
        if user_response.status_code != 200:
            logger.error(f"Failed to get user details: {user_response.status_code}")
            return jsonify({"error": "Failed to retrieve user details"}), 500
            
        user_data = user_response.json()
        user_details = user_data.get("details", {})
        user_name = user_details.get("name", "")
        user_email = user_details.get("email", "")
        user_address = f"{user_details.get('street1', '')}, {user_details.get('city', '')}, {user_details.get('state', '')} {user_details.get('zip', '')}"
        
        # Step 4: Get renter details
        renter_url = f"{USER_INFO_URL}?id={renter_id}"
        logger.info(f"Calling user service for renter at: {renter_url}")
        renter_response = requests.get(renter_url)
        logger.info(f"Renter response status: {renter_response.status_code}")
        
        if renter_response.status_code != 200:
            logger.error(f"Failed to get renter details: {renter_response.status_code}")
            return jsonify({"error": "Failed to retrieve renter details"}), 500
            
        renter_data = renter_response.json()
        renter_details = renter_data.get("details", {})
        renter_name = renter_details.get("name", "")
        renter_email = renter_details.get("email", "")
        renter_address = f"{renter_details.get('street1', '')}, {renter_details.get('city', '')}, {renter_details.get('state', '')} {renter_details.get('zip', '')}"
        
        # Step 5: Update order status to "shipping" in Order Records
        try:
            update_data = {"status": "shipping"}
            order_url = f"{ORDER_RECORDS_URL}/{order_id}"
            logger.info(f"Updating order #{order_id} status to 'shipping' at: {order_url}")
            
            update_response = requests.patch(order_url, json=update_data)
            logger.info(f"Order update response status: {update_response.status_code}")
            
            if update_response.status_code == 404:
                logger.error(f"Order #{order_id} not found")
                return jsonify({"error": "Order not found"}), 404
            elif update_response.status_code != 200:
                error_msg = f"Status {update_response.status_code} - {update_response.text[:100]}"
                logger.error(f"Update order status failed: {error_msg}")
                # Continue with notification even if status update fails
            else:
                logger.info(f"Updated order #{order_id} status to 'shipping'")
                
        except Exception as e:
            error_msg = str(e)[:100]
            logger.error(f"Order Records connection error: {error_msg}")
            logger.error(traceback.format_exc())
            # Continue with notification even if status update fails
        
        # Step 6: Send dual notification
        notification_data = {
            "orderID": order_id,
            "productID": product_id,
            "productName": product_name,
            "productDesc": product_desc,
            "userID": user_id,
            "userEmail": user_email,
            "userName": user_name,
            "userAddress": user_address,
            "renterID": renter_id,
            "renterEmail": renter_email,
            "renterName": renter_name,
            "renterAddress": renter_address,
            "trackingNumber": tracking_number,
            "shippingCarrier": carrier,
            "notificationType": "order_shipped"
        }

        # Get the base URL (everything up to and including the hostname:port)
        base_url = NOTIFICATION_URL.split('/notification/')[0]
        notification_url = f"{base_url}/notification/dual-email"
        logger.info(f"Using notification URL: {notification_url}")
        notification_response = requests.post(notification_url, json=notification_data)
                
        logger.info(f"Calling notification service at: {notification_url}")
        logger.info(f"Notification payload: {json.dumps(notification_data, indent=2)}")
        
        notification_response = requests.post(notification_url, json=notification_data)
        logger.info(f"Notification response status: {notification_response.status_code}")
        logger.info(f"Notification response body: {notification_response.text[:100]}")

        if notification_response.status_code not in [200, 201, 206]:
            logger.error(f"Failed to send notifications: {notification_response.status_code}")
            return jsonify({"error": "Failed to send notifications"}), 500
            
        notification_result = notification_response.json()
        
        # Return success response with shipping details
        response_data = {
            "message": "Shipping notifications sent successfully",
            "orderID": order_id,
            "trackingNumber": tracking_number,
            "carrier": carrier
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error in shipping notification: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "Error processing shipping notification"}), 500


if __name__ == '__main__':
    print("===== Order Communication Service Started =====")
    print("🔗 Endpoints configured:")
    print(f"  - Order Records: {ORDER_RECORDS_URL}")
    print(f"  - User Email: {USER_EMAIL_URL}")
    print(f"  - Product Details: {PRODUCT_DETAILS_URL}")
    print(f"  - Notification: {NOTIFICATION_URL}")
    print(f"  - RabbitMQ Host: {rabbitmq_host}")
    print(f"  - RabbitMQ Exchange: {exchange_name}")
    app.run(host='0.0.0.0',port=5001, debug=True)