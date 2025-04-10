from flask import Flask, request, jsonify
import stripe 
from firebase_config import db  # Firestore DB connection
import os
import requests
# import time
import sys
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)


# Load Stripe API Key from environment variables
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Create new StripeCusID and store in db
@app.route('/transaction/create-stripe-customer', methods=['POST'])
def create_stripe_customer():
    try:
        data = request.json
        user_id = data.get("userID")
        email = data.get("email")
        
        if not user_id or not email:
            return jsonify({"error": "Missing userID or email"}), 400

        # 🔍 Check if the user already has a Stripe customer
        existing_customer = db.collection('stripe_customers').document(str(user_id)).get()

        if existing_customer.exists:
            return jsonify({
                "error": f"Stripe customer already exists for userID {user_id}"
            }), 409

        # ✅ Use test token to create customer with attached card
        customer = stripe.Customer.create(
            email=email,
            source='tok_visa'  # Stripe test token
        )

        # ✅ Optional: set it as default in invoice settings
        stripe.Customer.modify(
            customer.id,
            invoice_settings={"default_payment_method": customer.default_source}
        )

        # Store in Firestore
        db.collection('stripe_customers').document(str(user_id)).set({
            "userID": user_id,
            "stripeCusID": customer.id,
            "email": email,
            "default_payment_method": customer.default_source
        })

        return jsonify({
            "message": "d",
            "stripeCusID": customer.id,
            "userID": user_id,
            "default_payment_method": customer.default_source
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/transaction/purchase', methods=['POST'])
def create_payment():
    try:
        order_data = request.json
        orderID = order_data.get("orderID")
        userID = order_data.get("userID")
        paymentAmt = order_data.get("paymentAmt")

        if not orderID or not userID or paymentAmt is None:
            app.logger.warning("❗ Missing required fields in request")
            return jsonify({"error": "Missing orderID, userID, or paymentAmt"}), 400

        app.logger.info(f"🔍 Searching for Stripe customer with userID: {userID}")

        stripe_customer_docs = db.collection('stripe_customers').where('userID', '==', userID).get()

        if not stripe_customer_docs:
            app.logger.error(f"❌ No Stripe customer found for userID {userID}")
            return jsonify({"error": f"No Stripe customer found for userID {userID}"}), 404

        stripe_customer_data = stripe_customer_docs[0].to_dict()

        stripeCusID = stripe_customer_data.get('stripeCusID')
        email = stripe_customer_data.get('email')
        default_pm = stripe_customer_data.get('default_payment_method')

        if not stripeCusID or not default_pm:
            app.logger.error(f"❌ Stripe customer record missing required fields for userID {userID}")
            return jsonify({"error": "Missing Stripe customer details"}), 400

        amount_in_cents = int(float(paymentAmt) * 100)

        app.logger.info(f"💳 Creating Stripe PaymentIntent for userID {userID}, {stripeCusID} amount {amount_in_cents} cents")

        payment_intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency='sgd',
            customer=stripeCusID,
            receipt_email=email,
            payment_method=default_pm,
            confirm=True,
            off_session=True
        )

        app.logger.info(f"✅ Stripe PaymentIntent created: {payment_intent.id}")

        # Store the transaction in Firestore
        transaction_ref = db.collection('transaction').document(payment_intent.id)
        transaction_ref.set({
            "orderID": orderID,
            "userID": userID,
            "paymentAmt": float(paymentAmt),  # store in dollars
            "status": "success",
            "email": email,
            "transactionID": payment_intent.id
        })

        app.logger.info(f"📝 Transaction saved to Firestore with ID {payment_intent.id}")

        return jsonify({
            "message": "Payment initiated",
            "transactionID": payment_intent.id,
            "orderID": orderID
        }), 200

    except stripe.error.CardError as ce:
        err = ce.error
        app.logger.warning(f"💳 Stripe CardError: {err.code} - {err.message}")
        return jsonify({
            "error": err.message,
            "code": err.code,
            "type": err.type
        }), 402

    except stripe.error.StripeError as se:
        app.logger.error(f"❌ Stripe API error: {str(se)}")
        return jsonify({"error": "A Stripe error occurred", "details": str(se)}), 500

    except Exception as e:
        app.logger.exception("❌ Unhandled exception in payment route")
        return jsonify({"error": str(e)}), 500


# Find transactionID by orderID and process refund
@app.route('/transaction/refund', methods=['POST'])
def refund_by_order_id():
    try:
        data = request.get_json()
        order_id = data.get('orderID')

        if not order_id:
            return jsonify({"error": "Missing orderID"}), 400

        # Step 1: Find the transaction by orderID
        transactions = db.collection('transaction').where('orderID', '==', order_id).get()

        if not transactions:
            return jsonify({"error": f"No transaction found for orderID {order_id}"}), 404
        if len(transactions) > 1:
            app.logger.warning(f"⚠️ More than one transaction found for orderID {order_id}. Using the first one.")

        transaction = transactions[0]
        transaction_data = transaction.to_dict()

        transaction_id = transaction_data.get('transactionID')
        payment_amt = transaction_data.get('paymentAmt')

        if not transaction_id or payment_amt is None:
            return jsonify({"error": "Incomplete transaction record"}), 400
        
        logging.debug(f"📝 Updating Firestore using transactionID as doc ID: {transaction_id}")
        # Step 2: Convert to cents (Stripe uses smallest currency unit)
        amount_in_cents = int(float(payment_amt) * 100)

        # Step 3: Create refund in Stripe
        refund = stripe.Refund.create(
            payment_intent=transaction_id,
            amount=amount_in_cents
        )

        # Step 4: Update Firestore
        try:
            transaction_ref = db.collection('transaction').document(transaction_id)
            transaction_ref.update({
                "status": "refunded",
                "refundID": refund.id
            })
            logging.debug(f"✅ Firestore document {transaction_id} updated successfully.")
        except Exception as update_error:
            logging.debug(f"🔥 Firestore update failed: {update_error}")
            return jsonify({"error": f"Firestore update failed: {str(update_error)}"}), 500

        return jsonify({
            "message": "Refund processed",
            "refundAmt": payment_amt,
            "refundID": refund.id,
            "orderID": order_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "Transaction Service is running"}), 200

if __name__ == '__main__':
    logging.debug("🚀 Flask app is running in Docker container!")
    app.run(host="0.0.0.0", port=5003)
