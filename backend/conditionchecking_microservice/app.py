import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import requests
import sys
import logging

# Setup logging to output to stdout
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Load environment variables from .env in the same folder as this file.
DOTENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(DOTENV_PATH)

import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize Firebase (Firestore) if the service account key is present.
service_account_path = os.environ.get("FIREBASE_CREDENTIALS", "serviceAccountKeyFirebase.json")
if os.path.exists(service_account_path):
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    db = None

# Dictionary of damage keywords -> deduction points
DAMAGE_DEDUCTIONS = {
    "scratch": 5, 
    "stain": 10,
    "dent": 10,
    "tear": 15,
    "crack": 20,
    "broken": 50,
}

DAMAGE_THRESHOLD = 30  # If newConditionScore < this, availability is set to False

def compare_images_via_zyla(url_image1, url_image2):
    """
    Calls the Zyla Image Similarity Calculator API via a GET request.
    Expected to return JSON with a similarity score ("confidence_score") and/or an "is_same" flag.
    """
    # Replace this endpoint with the exact URL from Zyla's docs.
    endpoint = "https://zylalabs.com/api/854/image+similarity+calculator+api/7488/get+similarity"
    
    headers = {
        # Ensure your ZYLA_API_KEY is correctly set in your environment
        "Authorization": f"{os.environ.get('ZYLA_API_KEY')}"
    }
    params = {
        "url1": url_image1,
        "url2": url_image2
    }

    response = requests.get(endpoint, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        logging.debug(f"Error calling similarity API: Status code {response.status_code}")
        logging.debug(f"Response: {response.text}")
        return None

@app.route("/compareImages", methods=["POST"])
def compare_images():
    """
    Expects a JSON payload like:
    {
      "productID": 123,
      "originalImageUrl": "https://example.com/item_before.jpg",
      "reportImageUrl": "https://example.com/item_after.jpg",
      "damageKeywords": ["scratch", "dent"],
      "conditionScore": 90,
      "availability": true
    }

    Flow:
      1. Call Zyla API to compare original and report images.
         - If the similarity result indicates dissimilarity (i.e., "is_same" is False),
           set availability to False regardless of the condition score.
      2. Deduct points based on damage keywords from the existing condition score.
      3. If the new condition score falls below DAMAGE_THRESHOLD, set availability to False.
      4. Store a record in Firestore with old/new condition scores, similarity result, etc.
      5. Return JSON with updated values and a success message.
    """
    data = request.get_json()
    product_id = data.get("productID")
    original_url = data.get("originalImageUrl")
    report_url = data.get("reportImageUrl")
    damage_keywords = data.get("damageKeywords", [])
    old_condition_score = data.get("conditionScore")  # from Inventory
    availability = data.get("availability", True)

    # Validate input
    missing_fields = []
    if not product_id:
        missing_fields.append("productID")
    if not original_url:
        missing_fields.append("originalImageUrl")
    if not report_url:
        missing_fields.append("reportImageUrl")
    if old_condition_score is None:
        missing_fields.append("conditionScore")
    
    if missing_fields:
        if "reportImageUrl" in missing_fields:
            error_message = "missing field in response"
        else:
            error_message = f"Missing required fields: {', '.join(missing_fields)}"
        logging.debug(f"❌ 400 Bad Request: {error_message}")
        logging.debug(f"🧾 Received payload: {data}")
        return jsonify({"error": error_message}), 400


    # 1. Call the Zyla similarity API to compare images.
    similarity_result = compare_images_via_zyla(original_url, report_url)
    if similarity_result:
        is_same = similarity_result.get("output").get("is_same")
        if is_same is not None:
            if not is_same:
                availability = False
    
    # 2. Compute new condition score using damage keywords.
    new_condition_score = old_condition_score
    found_keywords = []
    for kw in damage_keywords:
        kw_lower = kw.lower()
        if kw_lower in DAMAGE_DEDUCTIONS:
            deduction = DAMAGE_DEDUCTIONS[kw_lower]
            new_condition_score -= deduction
            found_keywords.append(kw_lower)
    new_condition_score = max(new_condition_score, 0)
    
    # 3. Further update availability if condition score falls below DAMAGE_THRESHOLD.
    if new_condition_score < DAMAGE_THRESHOLD:
        availability = False

    # 4. Store record in Firestore (optional)
    doc_id = None
    if db:
        doc_ref = db.collection("condition_checks").document()
        doc_data = {
            "productID": product_id,
            "originalImageUrl": original_url,
            "reportImageUrl": report_url,
            "oldConditionScore": old_condition_score,
            "newConditionScore": new_condition_score,
            "availability": availability,
            "damageKeywords": found_keywords,
            "similarityResult": similarity_result,
            "createdAt": datetime.now(timezone.utc)
        }
        doc_ref.set(doc_data)
        doc_id = doc_ref.id

    # 5. Return final JSON response with a success message.
    return jsonify({
        "message": "item condition score and availability updated successfully",
        "productID": product_id,
        "newConditionScore": new_condition_score,
        "availability": availability,
        "similarityResult": similarity_result,
        "firestoreDocID": doc_id
    }), 200

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
