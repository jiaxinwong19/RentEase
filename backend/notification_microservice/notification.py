import os
import json
import requests
import threading
import time
import pika
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS


# Load environment variables from .env
load_dotenv()

# Flask app initialization
app = Flask(__name__)
CORS(app)

# ZeptoMail configuration from environment variables
ZEPTOMAIL_API_URL = "https://api.zeptomail.com/v1.1/email"
API_KEY = os.getenv("ZEPTOMAIL_API_KEY")
MAIL_AGENT = os.getenv("MAIL_AGENT")
FROM_EMAIL = os.getenv("FROM_EMAIL")

# RabbitMQ connection details
# rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
exchange_name = os.getenv("EXCHANGE_NAME", "order_exchange")
queue_name = os.getenv("RABBITMQ_QUEUE", "unsuccessful_transaction_queue")
routing_key = "transaction.unsuccessful"

# Validate required environment variables
if not API_KEY or not FROM_EMAIL:
    app.logger.warning("Missing some environment variables. Check .env file.")

def send_email(to_email, subject, message):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Zoho-enczapikey {API_KEY}"
    }

    payload = {
        "from": {
            "address": FROM_EMAIL,
            "name": "RentEase"  # Customize sender name as needed
        },
        "to": [{
            "email_address": {
                "address": to_email,
                "name": "NoReply"  # Optional: Modify as needed
            }
        }],
        "subject": subject,
        "htmlbody": message  # Use htmlbody for email content
    }

    try:
        response = requests.post(ZEPTOMAIL_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        app.logger.error(f"ZeptoMail API Error: {response.status_code} - {response.text}")
        return {"error": f"ZeptoMail API Error: {response.status_code} - {response.text}"}, response.status_code
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request Error: {e}")
        return {"error": f"Request Error: {str(e)}"}, 500

# Enhanced logging setup
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.before_request
def log_request_info():
    logger.debug('Request Method: %s', request.method)
    logger.debug('Request Path: %s', request.path)
    logger.debug('Request Headers: %s', dict(request.headers))
    if request.is_json:
        logger.debug('Request JSON: %s', request.json)
    else:
        logger.debug('Request Body: %s', request.get_data(as_text=True))

@app.route("/notification/order/confirm", methods=["POST"])
def post_order():
    """Endpoint to post order data and send a confirmation email."""
    data = request.get_json()
 
    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    # Extract order details from the request body
    order_id = data.get("orderID")
    product_id = data.get("productID")
    prod_desc = data.get("prodDesc")
    original_image = data.get("originalImage")
    quantity = data.get("quantity", 1)  # Default to 1 if not provided
    user_id = data.get("userID")
    user_email = data.get("userEmail")

    # Validate required fields
    if not all([order_id, product_id, prod_desc, user_id, user_email]):
        return jsonify({"error": "Missing required fields"}), 400

    # Send the email notification to the user
    subject = "Order Confirmation"
    message = f"""
    <div>
        <h2>Order Confirmation</h2>
        <p>Dear User,</p>
        <p>Your order has been successfully placed!</p>
        <ul>
            <li><b>Order ID:</b> {order_id}</li>
            <li><b>Product:</b> {prod_desc}</li>
            <li><b>Quantity:</b> {quantity}</li>
        </ul>
        <p>Thank you for your purchase!</p>
    </div>
    """

    email_response = send_email(user_email, subject, message)

    if isinstance(email_response, tuple) and len(email_response) > 1 and "error" in email_response[0]:
        return jsonify({"error": "Failed to send email", "details": email_response[0]}), 500

    return jsonify({"success": "Order posted and email sent successfully!"}), 200


#endpoint for when shipping is confirmed, notify user and renter
@app.route('/notification/dual-email', methods=['POST'])
def dual_email_notification():
    """Endpoint to send notification emails to both the user and renter."""
    data = request.get_json()
    print("Received payload:", data)
    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400
    
    required_fields = [
        # Order information
        "orderID", "productID", "productName", "productDesc",
        # User information
        "userID", "userEmail", "userName", "userAddress",
        # Renter information
        "renterID", "renterEmail", "renterName", "renterAddress",
        # Shipping information
        "trackingNumber", "shippingCarrier",
        # Notification type
        "notificationType"
    ]
    
    # Check for missing required fields
    missing_fields = [field for field in required_fields if field not in data]
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    if missing_fields:
        error_message = f"Missing required fields: {', '.join(missing_fields)}"
        logger.error(error_message)
        return jsonify({"error": error_message}), 400
    
    # Get shipping information (now required)
    tracking_number = data["trackingNumber"]
    shipping_carrier = data["shippingCarrier"]
    
    # Determine notification type
    notification_type = data["notificationType"]
    
    # Send email to user
    user_subject = f"Your Order #{data['orderID']} - {notification_type.replace('_', ' ').title()}"
    user_message = f"""
    <div>
        <h2>Order {notification_type.replace('_', ' ').title()}</h2>
        <p>Dear {data['userName']},</p>
        
        <p>Your order details:</p>
        <ul>
            <li><b>Order ID:</b> {data['orderID']}</li>
            <li><b>Product:</b> {data['productName']}</li>
            <li><b>Description:</b> {data['productDesc']}</li>
        </ul>
        
        <h3>Shipping Information:</h3>
        <p>This item will be shipped from:</p>
        <p>{data['renterName']}<br>
        {data['renterAddress']}</p>
        
        <p><b>Tracking Number:</b> {tracking_number}<br>
        <b>Carrier:</b> {shipping_carrier}</p>
        
        <p>Thank you for your order!</p>
    </div>
    """
    
    user_email_result = send_email(data['userEmail'], user_subject, user_message)
    user_email_success = not (isinstance(user_email_result, tuple) and len(user_email_result) > 1 and "error" in user_email_result[0])
    
    # Send email to renter
    renter_subject = f"New Order #{data['orderID']} - {notification_type.replace('_', ' ').title()}"
    renter_message = f"""
    <div>
        <h2>New Order {notification_type.replace('_', ' ').title()}</h2>
        <p>Dear {data['renterName']},</p>
        
        <p>You have received a new order:</p>
        <ul>
            <li><b>Order ID:</b> {data['orderID']}</li>
            <li><b>Product:</b> {data['productName']}</li>
            <li><b>Description:</b> {data['productDesc']}</li>
        </ul>
        
        <h3>Shipping Information:</h3>
        <p>Please ship this item to:</p>
        <p>{data['userName']}<br>
        {data['userAddress']}</p>
        
        <p><b>Tracking Number:</b> {tracking_number}<br>
        <b>Carrier:</b> {shipping_carrier}</p>
        
        <p>Please ship this item within 24 hours if possible.</p>
        <p>Thank you!</p>
    </div>
    """
    
    renter_email_result = send_email(data['renterEmail'], renter_subject, renter_message)
    renter_email_success = not (isinstance(renter_email_result, tuple) and len(renter_email_result) > 1 and "error" in renter_email_result[0])
    
    # Return appropriate response based on email sending results
    if user_email_success and renter_email_success:
        return jsonify({"success": "Notifications sent successfully to both user and renter"}), 200
    elif user_email_success:
        return jsonify({"warning": "Notification sent to user but failed to notify renter"}), 206
    elif renter_email_success:
        return jsonify({"warning": "Notification sent to renter but failed to notify user"}), 206
    else:
        return jsonify({"error": "Failed to send notifications to both user and renter"}), 500


@app.route("/notification/payment/status", methods=["POST"])
def send_payment_notification():
    """Endpoint to send notifications about late charges or refunds."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    # Extract required fields
    user_email = data.get("userEmail")
    status = data.get("status")
    amount = data.get("amount")
    order_id = data.get("orderID")
    product_id = data.get("productID")

    # Validate required fields
    if not all([user_email, status, amount, order_id, product_id]):
        return jsonify({"error": "Missing required fields"}), 400

    if status not in ["late", "refund"]:
        return jsonify({"error": "Invalid status. Must be 'late' or 'refund'"}), 400

    # Prepare email content based on status
    if status == "late":
        subject = f"Late Return Charges - Order #{order_id}"
        message = f"""
        <div>
            <h2>Late Return Charges Notice</h2>
            <p>Dear Customer,</p>
            
            <p>This email is to inform you that late charges have been applied to your order #{order_id} 
            due to delayed return of the rented item ({product_id}).</p>
            
            <p>Late charges amount: ${amount}</p>
            
            <p>These charges have been automatically processed using your payment method on file.</p>
            
            <p>If you have any questions about these charges, please contact our customer support.</p>
            
            <p>Thank you for your understanding.</p>
        </div>
        """
    else:  # status == "refund"
        subject = f"Refund Processed - Order #{order_id}"
        message = f"""
        <div>
            <h2>Refund Notification</h2>
            <p>Dear Customer,</p>
            
            <p>We are pleased to inform you that a refund has been processed for your order #{order_id} - ({product_id}).</p>
            
            <p>Refund amount: ${amount}</p>
            
            <p>The refund will be credited to your original payment method. Please allow 3-5 business days 
            for the refund to appear in your account.</p>
            
            <p>Thank you for your business!</p>
        </div>
        """

    # Send the email
    email_result = send_email(user_email, subject, message)
    
    # Check if email was sent successfully
    if isinstance(email_result, tuple) and len(email_result) > 1 and "error" in email_result[0]:
        return jsonify({"error": "Failed to send notification email"}), 500
        
    return jsonify({"success": "Payment notification sent successfully"}), 200



@app.route("/notification/damage-report/isDamaged", methods=["POST"])
def post_damage_report():
    """Endpoint to post damage report data and send a notification email."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    # Extract damage report details from the request body
    report_id = data.get("reportID")
    user_id = data.get("userID")
    damage_type = data.get("damageType")
    description = data.get("description")
    product_id = data.get("productID")
    product_name = data.get("productName")
    user_email = data.get("userEmail")

    # Validate required fields
    if not all([report_id, user_id, damage_type, description, product_id, user_email]):
        return jsonify({"error": "Missing refund amount"}), 400

    # Determine refund or extra charges based on damage type
    if damage_type == "arrival":
        refund_amt = data.get("refundAmt")
        if not refund_amt:
            return jsonify({"error": "Missing refundAmt"}), 400
        subject = "Damage Report - Arrival"
        message = f"""
        <div>
            <h2>Damage Report - Arrival</h2>
            <p>Dear User,</p>
            <p>We have received your damage report.</p>
            <ul>
                <li><b>Report ID:</b> {report_id}</li>
                <li><b>Product ID:</b> {product_id}</li>
                <li><b>Product Name:</b> {product_name}</li>
                <li><b>Description:</b> {description}</li>
            </ul>
            <p>As the damage occurred during arrival, we have processed a full refund of ${refund_amt} to your account.</p>
            <p>We are truly sorry for any inconvenience caused.</p>
        </div>
        """
    elif damage_type == "user":
        subject = "Damage Report - User"
        message = f"""
        <div>
            <h2>Damage Report - User</h2>
            <p>Dear User,</p>
            <p>We have received your damage report.</p>
            <ul>
                <li><b>Report ID:</b> {report_id}</li>
                <li><b>Product ID:</b> {product_id}</li>
                <li><b>Product Name:</b> {product_name}</li>
                <li><b>Description:</b> {description}</li>
            </ul>
            <p>Since the damage occurred during use, we have deducted 20 points from your user score. You will face a temporary ban of 2 weeks if your score falls below 50.</p>
        </div>
        """
    else:
        return jsonify({"error": "Invalid damage type"}), 400

    # Send the email notification to the user
    email_response = send_email(user_email, subject, message)

    if isinstance(email_response, tuple) and len(email_response) > 1 and "error" in email_response[0]:
        return jsonify({"error": "Failed to send email", "details": email_response[0]}), 500

    return jsonify({"success": "Damage report posted and email sent successfully!"}), 200

@app.route("/notification/damage-report/notDamaged", methods=["POST"])
def post_no_damage_report():
    """Endpoint to notify user that item was inspected and found undamaged."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    # Extract required fields
    report_id = data.get("reportID")
    user_id = data.get("userID")
    product_id = data.get("productID")
    product_name = data.get("productName")
    description = data.get("description")
    user_email = data.get("userEmail")

    if not all([report_id, user_id, product_id, user_email]):
        return jsonify({"error": "Missing required fields"}), 400

    subject = "Damage Report Update - No Damage Found"
    message = f"""
    <div>
        <h2>Damage Report Update</h2>
        <p>Dear User,</p>
        <p>Thank you for submitting your damage report.</p>
        <ul>
            <li><b>Report ID:</b> {report_id}</li>
            <li><b>Product ID:</b> {product_id}</li><li><b>Product Name:</b> {product_name}</li>
            <li><b>Description:</b> {description}</li>
        </ul>
        <p>After thorough inspection, we are pleased to inform you that no damage was found on the item.</p>
        <p>No further action is required on your part.</p>
        <p>Thank you for your attention to product quality.</p>
    </div>
    """

    email_response = send_email(user_email, subject, message)

    if isinstance(email_response, tuple) and len(email_response) > 1 and "error" in email_response[0]:
        return jsonify({"error": "Failed to send email", "details": email_response[0]}), 500

    return jsonify({"success": "No damage confirmation sent successfully!"}), 200

@app.route("/notification/order/fail", methods=["POST"])
def payment_failure_notification():
    """Endpoint to handle payment failure notifications."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    # Extract order details from the request body
    order_id = data.get("orderID")
    user_id = data.get("userID")
    product_id = data.get("productID")
    product_desc = data.get("productDesc", "Unknown product")
    payment_amount = data.get("paymentAmount", 0)
    error_message = data.get("error", "An error occurred during payment processing")
    user_email = data.get("userEmail")

    # Validate required fields
    if not all([order_id, user_id, product_id, user_email]):
        missing = [field for field in ["orderID", "userID", "productID", "userEmail"] 
                  if not data.get(field)]
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # Send payment failure email
    subject = "Payment Failed - Order Processing Error"
    message = f"""
    <div>
        <h2>Payment Processing Failed</h2>
        <p>Dear User,</p>
        <p>We regret to inform you that there was an issue processing the payment for your recent order.</p>
        <ul>
            <li><b>Order ID:</b> {order_id}</li>
            <li><b>Product:</b> {product_desc}</li>
            <li><b>Amount:</b> ${payment_amount}</li>
            <li><b>Error:</b> {error_message}</li>
        </ul>
        <p>Please check your payment method and try again, or contact our support team for assistance.</p>
        <p>We apologize for any inconvenience caused.</p>
    </div>
    """

    email_response = send_email(user_email, subject, message)

    if isinstance(email_response, tuple) and len(email_response) > 1 and "error" in email_response[0]:
        return jsonify({"error": "Failed to send email", "details": email_response[0]}), 500

    return jsonify({"success": "Payment failure notification sent successfully!"}), 200

@app.route("/notification/renter/notify", methods=["POST"])
def notify_renter():
    """Endpoint to notify renters about new rental requests."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400
        
    # Required fields
    required_fields = ["renterEmail", "productID", "prodDesc", "originalImage", "orderID"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    # Extract data
    renter_email = data["renterEmail"]
    product_id = data["productID"]
    prod_desc = data["prodDesc"]
    original_image = data["originalImage"]
    order_id = data["orderID"]
    
    # Create email content
    subject = f"New Rental Request - Order #{order_id}"
    message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c5282;">New Rental Request</h2>
        <p>Hello,</p>
        <p>You have received a new rental request for your item!</p>
        
        <div style="background-color: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #4a5568; margin-top: 0;">Order Details</h3>
            <p><strong>Order ID:</strong> {order_id}</p>
            <p><strong>Product ID:</strong> {product_id}</p>
            <p><strong>Product Description:</strong> {prod_desc}</p>
            {f'<img src="{original_image}" alt="Product Image" style="max-width: 200px; margin-top: 10px;">' if original_image else ''}
        </div>
        
        <div style="background-color: #ebf8ff; padding: 20px; border-radius: 8px;">
            <h3 style="color: #2b6cb0; margin-top: 0;">Next Steps</h3>
            <ol style="color: #4a5568;">
                <li>Review the rental request</li>
                <li>Check your Orders page to accept or decline</li>
                <li>If accepted, prepare the item for shipping</li>
            </ol>
        </div>
        
        <p style="margin-top: 20px;">Please log in to your account to review and respond to this request.</p>
        <p>Thank you for using our platform!</p>
    </div>
    """
    
    # Send the email
    email_response = send_email(renter_email, subject, message)
    
    if isinstance(email_response, tuple) and len(email_response) > 1 and "error" in email_response[0]:
        app.logger.error(f"Failed to send email to {renter_email}: {email_response[0]}")
        return jsonify({
            "error": "Failed to send email",
            "details": email_response[0]
        }), 500
    
    app.logger.info(f"Successfully sent rental request notification to {renter_email}")
    return jsonify({
        "message": "Notification sent successfully",
        "orderID": order_id
    }), 200

@app.route("/notification/order/reject", methods=["POST"])
def order_rejection_notification():
    """Endpoint to send order rejection notifications to users."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    # Extract required fields
    order_id = data.get("orderID")
    user_email = data.get("userEmail")
    product_name = data.get("productName")
    rejection_reason = data.get("rejectionReason")

    # Validate required fields
    if not all([order_id, user_email, product_name, rejection_reason]):
        missing = [field for field in ["orderID", "userEmail", "productName", "rejectionReason"] 
                  if not data.get(field)]
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # Send rejection email
    subject = f"Order #{order_id} - Rejected"
    message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #e53e3e;">Order Rejected</h2>
        <p>Dear User,</p>
        <p>We regret to inform you that your order has been rejected by the renter.</p>
        
        <div style="background-color: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #4a5568; margin-top: 0;">Order Details</h3>
            <p><strong>Order ID:</strong> {order_id}</p>
            <p><strong>Product:</strong> {product_name}</p>
            <p><strong>Rejection Reason:</strong> {rejection_reason}</p>
        </div>
        
        <p>We apologize for any inconvenience caused. You may want to:</p>
        <ul style="color: #4a5568;">
            <li>Look for similar items from other renters</li>
            <li>Contact our support team if you have any questions</li>
        </ul>
        
        <p>Thank you for your understanding.</p>
    </div>
    """

    email_response = send_email(user_email, subject, message)

    if isinstance(email_response, tuple) and len(email_response) > 1 and "error" in email_response[0]:
        return jsonify({"error": "Failed to send email", "details": email_response[0]}), 500

    return jsonify({"success": "Rejection notification sent successfully!"}), 200

# RabbitMQ Setup
def setup_rabbitmq():
    """Set up RabbitMQ connection and channel"""
    try:
        rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
        channel = connection.channel()
        
        # Declare exchange and queue
        channel.exchange_declare(exchange=exchange_name, exchange_type="topic", durable=True)
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
        
        print(f"✅ Connected to RabbitMQ at 'rabbitmq'")
        print(f"✅ Listening on queue '{queue_name}' with routing key '{routing_key}'")
        
        return connection, channel
    except Exception as e:
        print(f"❌ Failed to connect to RabbitMQ: {str(e)}")
        return None, None

def process_rabbitmq_message(ch, method, properties, body):
    """Process a message from RabbitMQ using data directly from the message"""
    try:
        print(f"📩 Received message: {body}")
        data = json.loads(body)
        
        # Define all required fields for notification service
        required_fields = [
            "orderID", "userID", "productID", "productName", "productDesc", 
            "userEmail", "paymentAmount", "status"
        ]
        
        # Check for any missing fields
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Message missing required fields: {missing_fields}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        print(f"🔄 Processing notification for order #{data['orderID']}")
        
        # Create notification data directly from message without any defaults
        notification_data = {
            "orderID": data["orderID"],
            "userID": data["userID"],
            "userEmail": data["userEmail"],
            "productID": data["productID"],
            "productDesc": data["productDesc"],
            "productName": data["productName"],
            "originalImage": data.get("originalImage", ""),
            "paymentAmount": data["paymentAmount"],
            "status": data["status"]
        }
        
        # Add error message if present
        if "error" in data:
            notification_data["error"] = data["error"]
        
        # Determine which notification endpoint to use based on status
        if data["status"] == "error" or data["status"] == "payment_failed":
            notification_url = "http://localhost:5010/notification/order/fail"
        else:
            notification_url = "http://localhost:5010/notification/order/confirm"
        
        # Send notification using the appropriate endpoint
        try:
            response = requests.post(notification_url, json=notification_data)
            
            if response.status_code in [200, 201]:
                print(f"✅ Notification sent for order #{data['orderID']}")
            else:
                print(f"❌ Failed to send notification: Status {response.status_code}")
        except Exception as e:
            print(f"❌ Error sending notification: {str(e)}")
        
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"❌ Error processing message: {str(e)}")
        # Acknowledge to avoid blocking the queue
        ch.basic_ack(delivery_tag=method.delivery_tag)

# Start RabbitMQ consumer
def start_rabbitmq_consumer():
    """Start the RabbitMQ consumer in a loop with reconnection logic"""
    retry_count = 0
    max_retries = 10
    
    while retry_count < max_retries:
        try:
            connection, channel = setup_rabbitmq()
            
            if connection and channel:
                # Set up consumer with manual acknowledgment
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=process_rabbitmq_message,
                    auto_ack=False
                )
                
                print("🔄 Starting to consume messages. Press CTRL+C to exit")
                channel.start_consuming()
            else:
                retry_count += 1
                wait_time = retry_count * 5  # Increase wait time with each retry
                print(f"❌ Failed to setup RabbitMQ. Retrying in {wait_time} seconds... ({retry_count}/{max_retries})")
                time.sleep(wait_time)
                
        except pika.exceptions.AMQPConnectionError:
            retry_count += 1
            wait_time = retry_count * 5
            print(f"❌ RabbitMQ connection error. Retrying in {wait_time} seconds... ({retry_count}/{max_retries})")
            time.sleep(wait_time)
            
        except KeyboardInterrupt:
            if connection and connection.is_open:
                connection.close()
            break
            
        except Exception as e:
            print(f"❌ Unexpected error in RabbitMQ consumer: {str(e)}")
            retry_count += 1
            time.sleep(5)
    
    print("❌ Maximum retries reached. RabbitMQ consumer stopped.")

if __name__ == "__main__":
    # Start RabbitMQ consumer in a separate thread
    consumer_thread = threading.Thread(target=start_rabbitmq_consumer, daemon=True)
    consumer_thread.start()
    print("🔄 RabbitMQ consumer started in background thread")
    
    # Start Flask application
    app.run(debug=True, host="0.0.0.0", port=5010)
