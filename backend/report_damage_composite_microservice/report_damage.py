from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import uuid
import sys
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
app = Flask(__name__)
CORS(app)

# Mock URLs for demonstration (replace with actual service URLs)
INVENTORY_SERVICE_URL = os.environ.get("INVENTORY_SERVICE_URL")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL")
TRANSACTION_SERVICE_URL = os.environ.get("TRANSACTION_SERVICE_URL")
CONDITION_SERVICE_URL = os.environ.get("CONDITION_SERVICE_URL")
USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL")

# IMGUR_CLIENT_ID = os.environ.get("IMGUR_CLIENT_ID")

# # This must match the DAMAGE_DEDUCTIONS keys
KNOWN_DAMAGE_KEYWORDS = ["scratch", "stain", "dent", "tear", "crack", "broken"]

# get transactionID by orderID for refund purpose
# def get_transaction_id_by_order(order_id):
#     try:
#         logging.debug(f"🔍 Requesting transaction details for orderID: {order_id}")
#         response = requests.get(f"{TRANSACTION_SERVICE_URL}/transaction/{order_id}")
#         response.raise_for_status()
#         data = response.json()

#         transaction_id = data.get("transactionID")
#         payment_amt = data.get("paymentAmt")

#         logging.debug(f"✅ Retrieved transaction ID: {transaction_id}, Payment Amount: {payment_amt}")
#         return {
#             "transactionID": transaction_id,
#             "paymentAmt": payment_amt
#         }
#     except Exception as e:
#         logging.debug(f"❌ Failed to retrieve transaction info for order {order_id}: {e}")
#         return None

    
# get user email from userID for notif
def get_user_email(user_id):
    try:
        url = f"{USER_SERVICE_URL}/getEmail/?id={user_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        email = data.get("email")

        if email:
            return email
        else:
            logging.debug(f"⚠️ Email not found for user ID {user_id}")
            return None
    except Exception as e:
        logging.debug(f"❌ Error fetching email for user ID {user_id}: {e}")
        return None

# isolate damage keywords from description in report for condition checking

def extract_keywords(description: str):
    description = description.lower()
    return [kw for kw in KNOWN_DAMAGE_KEYWORDS if kw in description]

# get userID of person renting to update availability in inventory
def get_user_id_from_product(product_id):
    try:
        response = requests.get(f"{INVENTORY_SERVICE_URL}/inventory/products/{product_id}")
        response.raise_for_status()
        product_data = response.json()
        user_id = product_data.get("userID")
        
        if user_id is not None:
            return user_id
        else:
            logging.debug(f"⚠️ userID not found for product {product_id}")
            return None
    except Exception as e:
        logging.debug(f"❌ Error retrieving userID for product {product_id}: {str(e)}")
        return None

@app.route('/report-damage', methods=['POST'])
def submit_damage_report():
    report_id = str(uuid.uuid4())  # e.g. 'c9b1b9a2-8f35-4e56-bc7b-e52949ec7b6d'

    data = request.get_json()  # Use form to accept file uploads
    

    # Step 1: Parse required fields
    reportImage = data.get('reportImageUrl')
    user_id = data.get('userID') 
    product_id = data.get('productID')
    order_id = data.get('orderID')
    # title = data.get('title')
    description = data.get('description')
    damage_type = data.get('damageType') 
    # "arrival" or "use"
    
    # # 🔍 Extract keywords from description
    damage_keywords = extract_keywords(description) 
    
    # Step 2: Get original item image and score
    inventory_response = requests.get(f"{INVENTORY_SERVICE_URL}/inventory/products/{product_id}")
    if inventory_response.status_code != 200:
        return jsonify({"error": "Failed to fetch inventory details"}), 500
    inventory_data = inventory_response.json()
    product_name = inventory_data.get('productName')
    original_image = inventory_data.get('originalImageUrl')
    original_condition = inventory_data.get('conditionScore')
    availability = inventory_data.get('availability')
    
    logging.debug("📦 Inventory details received:")
    logging.debug(f"  - productName: {product_name}")
    logging.debug(f"  - originalImageUrl: {original_image}")
    logging.debug(f"  - conditionScore: {original_condition}")
    logging.debug(f"  - availability: {availability}")

    # Step 3: Send both images to condition checking service
    condition_payload = {
      "productID": product_id,
      "originalImageUrl": original_image,
      "reportImageUrl": reportImage,
      "damageKeywords": damage_keywords,
      "conditionScore": original_condition,
      "availability": availability
      
    }
    condition_response = requests.post(f"{CONDITION_SERVICE_URL}/compareImages", json=condition_payload)
    logging.debug(condition_response)
    new_condition = original_condition
    # # Handle response
    if condition_response.status_code == 200:
        condition_data = condition_response.json()
        new_condition = condition_data.get('newConditionScore')
        availability = condition_data.get('availability')
    else:
    # Handle errors gracefully
        logging.debug("❌ Failed to check condition:", condition_response.text)

    # Step 4: Update inventory with new condition


    logging.debug(availability)
    try:
        renterUID = get_user_id_from_product(product_id)
        inventory_payload = {
            "conditionScore": new_condition,
            "userID": renterUID
        }
        if availability == False:
            inventory_payload["availability"]=False
        inventory_upd_response = requests.put(
        f"{INVENTORY_SERVICE_URL}/inventory/products/{product_id}", json=inventory_payload)
        # )
        # if inventory_upd_response.code==200:
        #     logging.debug("availability updated")
        # else:
        #     logging.debug(f"❌ Failed to update inventory. Response: {inventory_response.text}")

    except requests.exceptions.RequestException as e:
            return jsonify({"error": "Failed to update product condition in inventory", "details": str(e)}), 500


    # Get email to send damage report assessment 
    user_email = get_user_email(user_id)

    # Step 6: Trigger refund or score penalty

    notif_payload = {
        "reportID": report_id,
        "userID": user_id,
        "description": description,
        "productID": product_id,
        "productName": product_name,
        "userEmail": user_email
    }

    if availability == False:
        logging.debug('availability is false and damagetype is arrival')
        if damage_type == "arrival":
            # Try to refund the user
            # transaction_info = get_transaction_id_by_order(order_id)
            # transactionID = None
            # paymentAmt = None


            # if transaction_info:
            #     transactionID = transaction_info.get("transactionID")
            #     paymentAmt = transaction_info.get("paymentAmt")

            refund_payload = {
                "orderID": order_id
            }
            refund_response = requests.post(f"{TRANSACTION_SERVICE_URL}/transaction/refund", json=refund_payload)
            

            if refund_response.status_code == 200:
                refund_data = refund_response.json()
                refundAmt = refund_data.get('refundAmt')
                logging.debug(refundAmt)
                notif_payload["refundAmt"] = refundAmt
                logging.debug(f"📦 Refund success. Response: {refund_response.json()}")
            else:
                logging.debug(f"❌ Refund failed. Response: {refund_response.text}")
        else:
            logging.debug('availability is false and damagetype is user')
            # Apply penalty to user
            penalty_payload = {
                "userID": user_id,
                "change": 20
            }
            penalty_response = requests.put(f"{USER_SERVICE_URL}/updateUserScore", json=penalty_payload)

            if penalty_response.status_code == 200:
                penalty_applied = True
                logging.debug("✅ User score deducted.")
            else:
                logging.debug(f"❌ Failed to deduct user score. Response: {penalty_response.text}")

        # Step 7: Notify user (item is damaged)
        notif_payload["damageType"] = damage_type  # Include only if damaged
        logging.debug("📨 Sending notification to /isDamaged endpoint")
        logging.debug(f"📤 Payload to Notification Service:\n{notif_payload}")

        notif_response = requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notification/damage-report/isDamaged",
            json=notif_payload
        )

        logging.debug(f"📥 Notification response status: {notif_response.status_code}")
        logging.debug(f"📥 Notification response body: {notif_response.text}")

        if notif_response.status_code == 400:
            return jsonify({
                "error": "Notification Service rejected request with 400",
                "details": notif_response.text,
                "payload": notif_payload
            }), 400

    else:
        # Step 7: Notify user (item undamaged)
        logging.debug("📨 Sending notification to /notDamaged endpoint")
        logging.debug(f"📤 Payload to Notification Service:\n{notif_payload}")

        notif_response = requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notification/damage-report/notDamaged",
            json=notif_payload
        )

        logging.debug(f"📥 Notification response status: {notif_response.status_code}")
        logging.debug(f"📥 Notification response body: {notif_response.text}")

        if notif_response.status_code == 400:
            return jsonify({
                "error": "Notification Service rejected request with 400",
                "details": notif_response.text,
                "payload": notif_payload
            }), 400




    return jsonify({"message": "Damage report submitted successfully"}), 200


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "Damage Report Service is running"}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5004)
