import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION (Pulled from Railway Variables) ---
# Use the Public URL of your proxy service
PROXY_URL = "https://openai-proxy-production-94e0.up.railway.app/v1/chat/completions"
PROXY_SECRET_KEY = os.getenv("PROXY_SECRET_KEY")

# Airtable Config
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")

@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
    
    file = request.files['file']
    
    # 1. Prepare the payload for the OpenAI Proxy
    # Note: We are assuming your proxy handles image-to-text conversion
    payload = {
        "model": "gpt-4o", 
        "messages": [
            {
                "role": "user",
                "content": "Extract the business name, phone number, and address from this lead image."
            }
        ]
    }

    # 2. Add the Secret Key 'Password' to the headers
    headers = {
        "Authorization": f"Bearer {PROXY_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # 3. Call the Proxy
        print(f"Calling Proxy at: {PROXY_URL}")
        resp = requests.post(PROXY_URL, json=payload, headers=headers, timeout=60)
        resp_data = resp.json()

        if resp.status_code != 200:
            return jsonify({"status": "error", "message": resp_data}), resp.status_code

        # 4. Extract data (Adjust this based on your Proxy's exact output)
        content = resp_data['choices'][0]['message']['content']

        # 5. Push to Airtable
        airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        at_headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}", "Content-Type": "application/json"}
        at_payload = {"fields": {"Raw Data": content}} # Adjust field name to match your table
        
        requests.post(airtable_url, json=at_payload, headers=at_headers)

        return jsonify({"status": "success", "data": content})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
