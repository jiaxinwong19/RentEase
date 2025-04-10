# Condition Checking Microservice

This microservice uses **Google Cloud Vision** to compare two images (original vs. newly uploaded) and returns a simple "damage severity score."

## 1. Prerequisites

- Python 3.9+
- Google Cloud account with Vision API enabled
- Service account key (JSON) downloaded
- Environment variable set:
  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service_account.json"

combined.py contains logic which app.py and similarity_test.py contain, right now, the logic by which avaiability of item is updated to false irregardless of condition score if similarity score by Zyla API is too low is not working properly yet.

Im not sure how to set similarity score threshold which determines what number it falls under for availability of that item to be considered false  