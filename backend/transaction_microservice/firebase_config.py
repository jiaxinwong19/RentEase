import firebase_admin
from firebase_admin import credentials, firestore

# Load Firebase credentials
cred = credentials.Certificate("serviceAccountKey.json")  # Your Firebase service account key
firebase_admin.initialize_app(cred)

# Firestore database reference
db = firestore.client()

