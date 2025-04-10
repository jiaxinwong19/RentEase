from flask import Flask, request, jsonify
import requests
import uuid
import json
import pika
from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "http://localhost:5173",  # Allow all origins in development
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": True,
        "send_wildcard": True
    }
})

# Service endpoints
ORDER_RECORDS_URL = "http://localhost:5000/orders"
USER_EMAIL_URL = "https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getEmail/"
PRODUCT_DETAILS_URL = "http://localhost:5020/inventory/products/"
NOTIFICATION_URL = "http://localhost:5010/notification/renter/notify"
ORDER_RECORDS_URL_GRAPHQL = "http://localhost:5000/graphql"

# RabbitMQ connection details
rabbitmq_host = "localhost"
exchange_name = "order_exchange"


        
@app.route('/order_com/orders', methods=['POST'])
def create_order():
    # Step 1: Get request data
    data = request.json
    print(f"📝 Received order request data for product: {data.get('productId')}")
    
    # Basic validation
    #PRICE IS FROM UI AFTER CALCULATION OF DAYS*PER DAY CHARGE
    required_fields = ['price', 'productId', 'renterID', 'startDate', 'endDate', 'userID']
    if not all(k in data for k in required_fields):
        missing_fields = [field for field in required_fields if field not in data]
        print(f"❌ Missing required fields: {missing_fields}")
        return jsonify({"error": "Missing required fields", "missing": missing_fields}), 400
    
    # Generate random numeric orderID
    order_id=str(uuid.uuid4())
    print(f"📌 Generated order ID: {order_id}")
    
    # Create order response
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
        print(f"📤 Posting order #{order_id} to Order Records")
        print(f"🔍 Order data being sent: {order_response}")
        print(f"📍 Sending to URL: {ORDER_RECORDS_URL}")
        
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
        "originalImage": original_image
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
    Publish comprehensive message data to RabbitMQ with all required fields
    
    Args:
        transaction_status: Either "successful" or "unsuccessful"
        message_data: Base transaction details
        order_id: Order ID for the transaction
        user_id: User ID for the transaction (user who is renting the item)
        product_id: Product ID for the transaction
    """
    try:
        # Get product details
        product_data = {}
        try:
            product_response = requests.get(f"{PRODUCT_DETAILS_URL}{product_id}")
            if product_response.status_code == 200:
                product_data = product_response.json()
                print(f"✅ Retrieved product details for message data")
            else:
                print(f"❌ Failed to get product details: Status {product_response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error getting product details: {str(e)[:100]}")
            return False
        
        # Get renter (owner) details - the person renting out the item
        renter_id = product_data.get("userID")
        renter_details = {}
        try:
            renter_info_response = requests.get(f"https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getUserInfo?id={renter_id}")
            if renter_info_response.status_code == 200:
                renter_details = renter_info_response.json().get("details", {})
                print(f"✅ Retrieved renter details for message data")
            else:
                print(f"❌ Failed to get renter details: Status {renter_info_response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error getting renter details: {str(e)[:100]}")
            return False
        
        # Get user (recipient) details - the person renting the item
        user_details = {}
        try:
            user_info_response = requests.get(f"https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getUserInfo?id={user_id}")
            if user_info_response.status_code == 200:
                user_details = user_info_response.json().get("details", {})
                print(f"✅ Retrieved user details for message data")
            else:
                print(f"❌ Failed to get user details: Status {user_info_response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error getting user details: {str(e)[:100]}")
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
            "senderEmail": renter_details.get("email", "")
        }
        
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
        channel = connection.channel()
        
        # Define the routing key based on status
        routing_key = f"transaction.{transaction_status}"
        
        # Publish the message
        channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(complete_message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )
        
        print(f"✅ Published complete {transaction_status} transaction event for order #{order_id}")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Failed to publish RabbitMQ message: {str(e)}")
        return False

@app.route('/order_com/confirm/<string:order_id>', methods=['POST'])
def confirm_order(order_id):
    """
    Endpoint for renters to confirm pending orders
    """
    print(f"📝 Processing confirmation for order #{order_id}")
    
    try:        
        # Update order status to accepted 
        try:
            update_data = {"status": "accepted"}
            order_url = f"{ORDER_RECORDS_URL}/{order_id}"
            print(f"🔄 Updating order #{order_id} status to 'accepted'")
            
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
            
        # Get stripeCusID from the specific stripe ID endpoint
        try:
            print(f"💳 Getting Stripe customer ID for user #{user_id}")
            stripe_response = requests.get(f"https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getStripeCusID/?id={user_id}")
            
            if stripe_response.status_code != 200:
                error_msg = f"Status {stripe_response.status_code} - {stripe_response.text[:100]}"
                print(f"❌ Stripe customer ID lookup failed: {error_msg}")
                return jsonify({"error": f"Failed to retrieve stripe customer ID: {error_msg}"}), 500
                    
            stripe_data = stripe_response.json()
            stripe_cus_id = stripe_data.get("stripeCusID")
            
            if not stripe_cus_id:
                print(f"❌ User #{user_id} has no Stripe customer ID")
                return jsonify({"error": "User does not have a Stripe customer ID"}), 400
                
            print(f"✅ Retrieved Stripe customer ID for user #{user_id}")
                
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"❌ Stripe service connection error: {error_msg}")
            return jsonify({"error": f"Error retrieving Stripe customer ID: {error_msg}"}), 500

        # Process the transaction with the retrieved Stripe customer ID
        try:
            # Prepare data for transaction endpoint
            transaction_data = {
                "orderID": order_id,
                "userID": user_id,
                "paymentAmt": payment_amount,  # Renamed from paymentAmount to paymentAmt
                "stripeCusID": stripe_cus_id
            }
            
            print(f"💰 Processing payment of ${payment_amount} for order #{order_id}")
            
            # Send data to transaction endpoint
            transaction_response = requests.post(
                "http://localhost:5003/transaction/purchase",
                json=transaction_data
            )
            
            # Prepare base message data
            base_message_data = {
                "orderID": order_id,
                "userID": user_id,
                "paymentAmount": payment_amount,
                "stripeCusID": stripe_cus_id,
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
                "stripeCusID": stripe_cus_id,
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

@app.route('/order_com/notify-shipping/<string:order_id>', methods=['POST'])
def notify_shipping_details(order_id):
    """Send shipping notifications to both user and renter"""
    print(f"Processing shipping notification for order #{order_id}")
    
    try:
        # Step 1: Get shipping information
        shipping_response = requests.get(f"http://localhost:5009/shipping/{order_id}")
        if shipping_response.status_code != 200:
            print(f"Failed to get shipping data: {shipping_response.status_code}")
            return jsonify({"error": "Failed to retrieve shipping data"}), 500
            
        shipping_data = shipping_response.json()
        tracking_number = shipping_data.get("tracking_number")
        carrier = shipping_data.get("carrier", "USPS")
        user_id = shipping_data.get("user_id")
        renter_id = shipping_data.get("renter_id")
        product_id = shipping_data.get("product_id")

        print(f"DEBUG - Shipping data received for order {order_id}:")
        print(json.dumps(shipping_data, indent=2))
        
        required_fields = ["tracking_number", "user_id", "renter_id", "product_id"]
        missing_fields = [field for field in required_fields if not shipping_data.get(field)]
        print(f"DEBUG - Missing required shipping fields: {missing_fields}")
        
        if not all([tracking_number, user_id, renter_id, product_id]):
            print(f"Shipping data incomplete")
            
            return jsonify({"error": "Incomplete shipping data"}), 400
            
        # Step 2: Get product details
        product_response = requests.get(f"{PRODUCT_DETAILS_URL}{product_id}")
        if product_response.status_code != 200:
            print(f"Failed to get product details: {product_response.status_code}")
            return jsonify({"error": "Failed to retrieve product details"}), 500
            
        product_data = product_response.json()
        product_name = product_data.get("productName", "")
        product_desc = product_data.get("productDesc", "")
        
        # Step 3: Get user details
        user_response = requests.get(f"https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getUserInfo?id={user_id}")
        if user_response.status_code != 200:
            print(f"Failed to get user details: {user_response.status_code}")
            return jsonify({"error": "Failed to retrieve user details"}), 500
            
        user_data = user_response.json()
        user_details = user_data.get("details", {})
        user_name = user_details.get("name", "")
        user_email = user_details.get("email", "")
        user_address = f"{user_details.get('street1', '')}, {user_details.get('city', '')}, {user_details.get('state', '')} {user_details.get('zip', '')}"
        
        # Step 4: Get renter details
        renter_response = requests.get(f"https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getUserInfo?id={renter_id}")
        if renter_response.status_code != 200:
            print(f"Failed to get renter details: {renter_response.status_code}")
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
            print(f"🔄 Updating order #{order_id} status to 'shipping'")
            
            update_response = requests.patch(order_url, json=update_data)
            
            if update_response.status_code == 404:
                print(f"❌ Order #{order_id} not found")
                return jsonify({"error": "Order not found"}), 404
            elif update_response.status_code != 200:
                error_msg = f"Status {update_response.status_code} - {update_response.text[:100]}"
                print(f"❌ Update order status failed: {error_msg}")
                # Continue with notification even if status update fails
            else:
                print(f"✅ Updated order #{order_id} status to 'shipping'")
                
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"❌ Order Records connection error: {error_msg}")
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
        
        notification_response = requests.post("http://localhost:5010/notification/dual-email", json=notification_data)
        if notification_response.status_code not in [200, 201, 206]:
            print(f"Failed to send notifications: {notification_response.status_code}")
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
        print(f"Error in shipping notification: {str(e)}")
        return jsonify({"error": "Error processing shipping notification"}), 500


if __name__ == '__main__':
    print("===== Order Communication Service Started =====")
    print(f"🔗 Endpoints configured:")
    print(f"  - Order Records: {ORDER_RECORDS_URL}")
    print(f"  - User Email: {USER_EMAIL_URL}")
    print(f"  - Product Details: {PRODUCT_DETAILS_URL}")
    print(f"  - Notification: {NOTIFICATION_URL}")
    print(f"  - RabbitMQ Host: {rabbitmq_host}")
    print(f"  - RabbitMQ Exchange: {exchange_name}")
    app.run(port=5001, debug=True)