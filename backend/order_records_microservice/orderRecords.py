import os
import graphene
from flask import Flask, jsonify, request
from flask_graphql import GraphQLView
from google.cloud import firestore
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
COLLECTION_NAME = os.getenv("FIRESTORE_COLLECTION", "default_collection")

app = Flask(__name__)

def get_firestore_client():
    return firestore.Client()

def convert_order_data(data: dict) -> dict:
    for key in ["startDate", "endDate"]:
        if key in data and isinstance(data[key], datetime):
            data[key] = data[key].isoformat()
    return data

class Order(graphene.ObjectType):
    orderID = graphene.String()
    paymentAmount = graphene.Float()
    dailyPayment = graphene.Float()
    productID = graphene.Int()
    renterID = graphene.Int()
    startDate = graphene.String()
    endDate = graphene.String()
    status = graphene.String()
    userID = graphene.Int()

class Query(graphene.ObjectType):
    orders = graphene.List(Order)
    order = graphene.Field(Order, orderID=graphene.String(required=True))
    overdueOrders = graphene.List(Order)
    ordersByUser = graphene.List(Order, userID=graphene.Int(required=True))
    ordersByRenter = graphene.List(Order, renterID=graphene.Int(required=True))

    def resolve_orders(self, info):
        try:
            db = get_firestore_client()
            docs = db.collection(COLLECTION_NAME).stream()
            return [Order(**convert_order_data(doc.to_dict())) for doc in docs]
        except Exception as e:
            print(f"Error in resolve_orders: {e}")
            return []

    def resolve_order(self, info, orderID):
        try:
            db = get_firestore_client()
            docs = db.collection(COLLECTION_NAME).where("orderID", "==", orderID).stream()
            for doc in docs:
                return Order(**convert_order_data(doc.to_dict()))
            return None
        except Exception as e:
            print(f"Error in resolve_order: {e}")
            return None

    def resolve_overdueOrders(self, info):
        try:
            db = get_firestore_client()
            now = datetime.now(timezone.utc)
            orders_list = []
            seen_ids = set()
            for doc in db.collection(COLLECTION_NAME).where("status", "==", "late").stream():
                if doc.id not in seen_ids:
                    orders_list.append(Order(**convert_order_data(doc.to_dict())))
                    seen_ids.add(doc.id)
            for doc in db.collection(COLLECTION_NAME).where("status", "==", "paid").stream():
                data = doc.to_dict()
                if isinstance(data.get("endDate"), datetime) and data["endDate"] < now and doc.id not in seen_ids:
                    orders_list.append(Order(**convert_order_data(data)))
                    seen_ids.add(doc.id)
            return orders_list
        except Exception as e:
            print(f"Error in resolve_overdueOrders: {e}")
            return []

    def resolve_ordersByUser(self, info, userID):
        try:
            db = get_firestore_client()
            docs = db.collection(COLLECTION_NAME).where("userID", "==", userID).stream()
            return [Order(**convert_order_data(doc.to_dict())) for doc in docs]
        except Exception as e:
            print(f"Error in resolve_ordersByUser: {e}")
            return []

    def resolve_ordersByRenter(self, info, renterID):
        try:
            db = get_firestore_client()
            docs = db.collection(COLLECTION_NAME).where("renterID", "==", renterID).stream()
            return [Order(**convert_order_data(doc.to_dict())) for doc in docs]
        except Exception as e:
            print(f"Error in resolve_ordersByRenter: {e}")
            return []

class UpdateOrderStatus(graphene.Mutation):
    class Arguments:
        orderID = graphene.String(required=True)
        status = graphene.String(required=True)

    orderID = graphene.String()
    status = graphene.String()
    ok = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, orderID, status):
        try:
            db = firestore.Client()
            docs = db.collection(COLLECTION_NAME).where("orderID", "==", orderID).stream()
            updated = False
            for doc in docs:
                doc.reference.update({"status": status})
                updated = True
            if updated:
                return UpdateOrderStatus(orderID=orderID, status=status, ok=True, message="Status updated")
            else:
                return UpdateOrderStatus(ok=False, message="Order not found")
        except Exception as e:
            return UpdateOrderStatus(ok=False, message=str(e))

class Mutation(graphene.ObjectType):
    update_order_status = UpdateOrderStatus.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True)
)

@app.route('/orders', methods=['POST'])
def create_order_rest():
    try:
        data = request.get_json()
        required_fields = ["orderID", "paymentAmount", "productID", "renterID", "startDate", "endDate", "status", "userID"]
        
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Convert string dates to datetime
        start_date = datetime.fromisoformat(data["startDate"])
        end_date = datetime.fromisoformat(data["endDate"])
        
        duration_days = (end_date.date() - start_date.date()).days
        if duration_days <= 0:
            return jsonify({"error": "Invalid rental period"}), 400
        
        daily_payment = round(float(data["paymentAmount"]) / duration_days, 2)
        
        # Create order document
        order_doc = {
            "orderID": data["orderID"],
            "paymentAmount": float(data["paymentAmount"]),
            "productID": int(data["productID"]),
            "renterID": int(data["renterID"]),
            "startDate": start_date,
            "endDate": end_date,
            "status": data["status"],
            "userID": int(data["userID"]),
            "dailyPayment": daily_payment
        }

        db = get_firestore_client()
        db.collection(COLLECTION_NAME).add(order_doc)
        return jsonify({"message": "Order created successfully"}), 201

    except Exception as e:
        print(f"❌ Error in create_order_rest: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/orders/<order_id>', methods=['PATCH'])
def update_order_status_rest(order_id):
    try:
        data = request.json
        new_status = data.get("status")

        if not new_status:
            return jsonify({"error": "Missing status field"}), 400

        db = get_firestore_client()
        docs = db.collection(COLLECTION_NAME).where("orderID", "==", order_id).stream()

        updated = False
        for doc in docs:
            doc.reference.update({"status": new_status})
            updated = True

        if updated:
            return jsonify({"message": "Order status updated", "orderID": order_id, "newStatus": new_status}), 200
        else:
            return jsonify({"error": "Order not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)