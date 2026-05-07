import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION (Pulled from Railway Variables) ---
PROXY_URL = "https://openai-proxy-production-94e0.up.railway.app/v1/chat/completions"
PROXY_SECRET_KEY = os.getenv("PROXY_SECRET_KEY")

# Airtable Config
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")

@app.route('/process', methods=['POST'])
def process():
    # 1. Validation Checks
    if not PROXY_SECRET_KEY:
        return jsonify({"status": "error", "message": "PROXY_SECRET_KEY is missing from Railway variables"}), 500
    
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
    
    file = request.files['file']
    
    # 2. Prepare the payload for the OpenAI Proxy
    payload = {
        "model": "gpt-4o", 
        "messages": [
            {
                "role": "user",
                "content": "Extract the business name, phone number, and address from this lead image."
            }
        ]
    }

    # 3. Add the Secret Key 'Password' to the headers
    proxy_headers = {
        "Authorization": f"Bearer {PROXY_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # 4. Call the Proxy
        print(f"Calling Proxy at: {PROXY_URL}")
        resp = requests.post(PROXY_URL, json=payload, headers=proxy_headers, timeout=60)
        
        if resp.status_code != 200:
            return jsonify({"status": "error", "message": f"Proxy Error: {resp.text}"}), resp.status_code

        resp_data = resp.json()
        content = resp_data['choices'][0]['message']['content']

        # 5. Push to Airtable (Fixed Payload Structure)
        airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        at_headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}", 
            "Content-Type": "application/json"
        }
        
        # Airtable REQUIRES a 'records' list
        at_payload = {
            "records": [
                {
                    "fields": {
                        "Raw Data": content  # Make sure this column name matches Airtable EXACTLY
                    }
                }
            ]
        }
        
        at_resp = requests.post(airtable_url, json=at_payload, headers=at_headers)
        
        if at_resp.status_code != 200:
            print(f"Airtable Error: {at_resp.text}")

        return jsonify({"status": "success", "data": content})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Railway uses the PORT environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
