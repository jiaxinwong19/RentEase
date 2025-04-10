import os
import uuid
import requests
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configurable endpoints via environment variables
USER_SERVICE_BASE_URL = os.getenv("USER_SERVICE_BASE_URL")  # e.g., https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user
INVENTORY_SERVICE_API = os.getenv("INVENTORY_SERVICE_API", "http://inventory-app:5020")
TRANSACTION_SERVICE_BASE_URL = os.getenv("TRANSACTION_SERVICE_BASE_URL", "http://transaction-service:5003")

@app.route('/lateCharge', methods=['POST'])
def handle_late_charge():
    """
    Receives JSON data from the Check Expiry service:
    {
      "dailyPayment": <Number>,
      "renterID": <Number>,
      "userID": <Number>,
      "productID": <Number>,
      "overdue14": <Boolean>
    }
    
    Process:
      1. Retrieve userScore from the User service:
         GET {USER_SERVICE_BASE_URL}/getUserScore/?id={userID}
      2. Retrieve product details from the Inventory service:
         GET {INVENTORY_SERVICE_API}/inventory/products/{productID}
         to obtain "price" and "productName".
      3. If overdue14 is true, use the retrieved "price" for calculation;
         otherwise, use the provided "dailyPayment".
      4. Calculate lateCharge = round((value * 100) / userScore, 2)
         where value is either the retrieved price or dailyPayment.
      5. Immediately return:
         { "lateCharge": <calculated_value>, "productName": <retrieved_productName> }
      6. In a background thread, perform:
         a. GET {USER_SERVICE_BASE_URL}/getStripeCusID/?id={userID} to obtain stripeCusID.
         b. Generate a random orderID.
         c. POST to {TRANSACTION_SERVICE_BASE_URL}/transaction/purchase with JSON:
            {
              "orderID": <random string>,
              "paymentAmt": <lateCharge>,
              "userID": "<userID as string>",
              "stripeCusID": <retrieved stripeCusID>
            }
         (No response is handled from this POST request.)
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ["dailyPayment", "renterID", "userID", "productID", "overdue14"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    try:
        user_id = data.get("userID")
        daily_payment = data.get("dailyPayment")
        product_id = data.get("productID")
        overdue14 = data.get("overdue14")
        
        # Retrieve userScore from the User service
        user_url = f"{USER_SERVICE_BASE_URL}/getUserScore/?id={user_id}"
        user_resp = requests.get(user_url, timeout=10)
        user_resp.raise_for_status()
        user_data = user_resp.json()
        user_score = user_data.get("userScore")
        if not user_score:
            return jsonify({"error": "Invalid userScore received"}), 500

        # Always retrieve product details from Inventory service
        inventory_url = f"{INVENTORY_SERVICE_API}/inventory/products/{product_id}"
        inv_resp = requests.get(inventory_url, timeout=10)
        inv_resp.raise_for_status()
        inv_data = inv_resp.json()
        product_name = inv_data.get("productName")
        price = inv_data.get("price")
        if price is None or not product_name:
            return jsonify({"error": "Invalid product details received from Inventory service"}), 500

        # Determine value for calculation: use price if overdue14 is true; otherwise, use dailyPayment.
        value_for_calc = price if overdue14 else daily_payment

        late_charge = round(value_for_calc * 100 / user_score, 2)
        response_data = {"lateCharge": late_charge, "productName": product_name}

        # Start background transaction processing (fire-and-forget)
        threading.Thread(target=process_transaction, args=(user_id, late_charge)).start()

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process_transaction(user_id, late_charge):
    """
    In a background thread, performs:
      1. Generates a random orderID.
      2. Sends a POST request to Transaction service at:
         {TRANSACTION_SERVICE_BASE_URL}/transaction/purchase
         with JSON payload:
         {
           "orderID": <random string>,
           "paymentAmt": late_charge,
           "userID": "<userID as string>"
         }
         (The response is not processed; the request is fire-and-forget.)
    """
    try:
        order_id = str(uuid.uuid4())

        transaction_payload = {
            "orderID": order_id,
            "paymentAmt": late_charge,
            "userID": str(user_id)
        }

        transaction_url = f"{TRANSACTION_SERVICE_BASE_URL}/transaction/purchase"
        # Fire-and-forget POST request; no response handling.
        requests.post(transaction_url, json=transaction_payload, timeout=10)
    except Exception:
        pass  # Silently ignore background errors

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)