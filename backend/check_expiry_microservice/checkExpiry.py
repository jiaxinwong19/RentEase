import os
import requests
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone, timedelta

# Load environment variables
load_dotenv()
BASE_URL = os.getenv("ORDER_RECORDS_API")  # e.g., http://order-records:5000
GRAPHQL_URL = f"{BASE_URL}/graphql"
UPDATE_URL = f"{BASE_URL}/orders"  # for REST PATCH updates
LATE_CHARGE_URL = os.getenv("LATE_CHARGE_URL")  # e.g., http://late-charge:5001/lateCharge
USER_SERVICE_API = os.getenv("USER_SERVICE_API", "https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user")
USER_UPDATE_ENDPOINT = f"{USER_SERVICE_API}/updateUserScore"
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL")  # e.g., http://notification:5010/notification/payment/status

# Retrieve trigger time from environment variables (defaults: hour=0, minute=0)
TRIGGER_HOUR = int(os.getenv("TRIGGER_HOUR", 0))
TRIGGER_MINUTE = int(os.getenv("TRIGGER_MINUTE", 0))
TIMEZONE = "Asia/Singapore"  # Allowed to remain hardcoded

def update_order_status(order_id, new_status):
    """Updates the order's status by sending a PATCH request."""
    url = f"{UPDATE_URL}/{order_id}"
    try:
        response = requests.patch(url, json={"status": new_status}, timeout=10)
        response.raise_for_status()
    except Exception:
        pass

def update_user_score(order):
    """Updates the user score by sending a PUT request to the User service."""
    payload = {
        "userID": order.get("userID"),
        "change": 5
    }
    try:
        response = requests.put(USER_UPDATE_ENDPOINT, json=payload, timeout=10)
        response.raise_for_status()
    except Exception:
        pass

def send_to_late_charge_and_get_response(order):
    """
    Sends late charge data to the Late Charge service and returns its JSON response.
    The payload includes:
      dailyPayment, renterID, userID, productID, and overdue14.
    """
    if not LATE_CHARGE_URL:
        return None

    payload = {
        "dailyPayment": order.get("dailyPayment"),
        "renterID": order.get("renterID"),
        "userID": order.get("userID"),
        "productID": order.get("productID"),
        "overdue14": order.get("overdue14", False)
    }
    try:
        resp = requests.post(LATE_CHARGE_URL, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()  # Expected to return { "lateCharge": <value>, "productName": <value> }
    except Exception:
        return None

def get_user_email(user_id):
    """
    Retrieves user email from the User service via:
      GET {USER_SERVICE_API}/getEmail/?id={user_id}
    Expected JSON response: { "email": "<userEmail>", ... }
    """
    email_url = f"{USER_SERVICE_API}/getEmail/?id={user_id}"
    try:
        resp = requests.get(email_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("email")
    except Exception:
        return None

def send_to_notification(order, late_charge):
    """
    Sends notification to the Notification service.
    If an order is overdue for more than 14 days (marked "completed" in the system),
    the status is converted to "refund" in the notification payload.
    """
    if not NOTIFICATION_SERVICE_URL:
        return

    user_email = get_user_email(order.get("userID"))
    if not user_email:
        return

    status = order.get("status")
    if status == "completed" and order.get("overdue14"):
        status = "late"

    payload = {
        "userEmail": user_email,
        "status": status,
        "amount": late_charge,
        "orderID": order.get("orderID"),
        "productID": order.get("productID")
    }
    try:
        requests.post(NOTIFICATION_SERVICE_URL, json=payload, timeout=10)
    except Exception:
        pass

def fetch_and_update_orders():
    """
    Retrieves overdue orders via the GraphQL endpoint.
    For each order:
      - Checks if the order is >14 days overdue.
      - Updates the order's status:
           * Sets to "completed" if >14 days overdue.
           * Sets to "late" if not >14 days overdue and current status is not "late".
      - Updates the user score.
      - Adds a Boolean field 'overdue14' to the order payload.
      - Sends the late charge data to the Late Charge service and receives its response.
      - Posts a notification to the Notification service using the late charge amount and order details.
    """
    query = """
    query {
      overdueOrders {
        orderID
        dailyPayment
        productID
        renterID
        endDate
        status
        userID
      }
    }
    """
    try:
        resp = requests.post(GRAPHQL_URL, json={"query": query}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        orders = data.get("data", {}).get("overdueOrders", [])
        now = datetime.now(timezone.utc)
        for order in orders:
            order_id = order.get("orderID")
            current_status = order.get("status", "").lower()
            try:
                order_end_date = datetime.fromisoformat(order.get("endDate"))
            except Exception:
                continue

            overdue_threshold = order_end_date + timedelta(days=14)
            is_overdue_14 = now > overdue_threshold

            if is_overdue_14:
                if current_status != "completed":
                    update_order_status(order_id, "completed")
                    order["status"] = "completed"
            else:
                if current_status != "late":
                    update_order_status(order_id, "late")
                    order["status"] = "late"

            update_user_score(order)
            order["overdue14"] = is_overdue_14

            # Send to Late Charge service and get its response
            lc_response = send_to_late_charge_and_get_response(order)
            if lc_response is None or "lateCharge" not in lc_response:
                continue

            late_charge = lc_response["lateCharge"]
            product_name = lc_response.get("productName")
            order["productName"] = product_name

            # Now, POST to Notification service with the late charge details
            send_to_notification(order, late_charge)

    except Exception:
        pass

def main():
    scheduler = BlockingScheduler()
    trigger = CronTrigger(hour=TRIGGER_HOUR, minute=TRIGGER_MINUTE, timezone=TIMEZONE)
    scheduler.add_job(fetch_and_update_orders, trigger)
    scheduler.start()

if __name__ == "__main__":
    main()