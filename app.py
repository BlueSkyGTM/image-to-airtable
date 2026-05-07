import os
import requests
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
PROXY_URL = "https://openai-proxy-production-94e0.up.railway.app/v1/chat/completions"
PROXY_SECRET_KEY = os.getenv("PROXY_SECRET_KEY")

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")

@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
    
    file = request.files['file']
    
    # 1. Convert image to Base64 so the Proxy/OpenAI can 'see' it
    image_base64 = base64.b64encode(file.read()).decode('utf-8')
    
    # 2. Correct Payload for GPT-4o with Vision
    payload = {
        "model": "gpt-4o", 
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the business name, phone number, and address from this lead. Return only the data."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        ],
        "max_tokens": 500
    }

    # 3. USE THE CORRECT HEADER: X-Proxy-Auth
    proxy_headers = {
        "X-Proxy-Auth": PROXY_SECRET_KEY,
        "Content-Type": "application/json"
    }

    try:
        # 4. Call the Proxy
        resp = requests.post(PROXY_URL, json=payload, headers=proxy_headers, timeout=60)
        
        if resp.status_code != 200:
            return jsonify({"status": "error", "message": f"Proxy Error: {resp.text}"}), resp.status_code

        resp_data = resp.json()
        content = resp_data['choices'][0]['message']['content']

        # 5. Push to Airtable
        airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        at_headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}", 
            "Content-Type": "application/json"
        }
        
        at_payload = {
            "records": [{"fields": {"Raw Data": content}}]
        }
        
        requests.post(airtable_url, json=at_payload, headers=at_headers)

        return jsonify({"status": "success", "data": content})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
