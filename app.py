import os
import json
import base64
import requests
from flask import Flask, request, jsonify
from pyairtable import Api

app = Flask(__name__)

# --- CONFIG (From Railway Variables) ---
PROXY_URL = os.getenv("PROXY_URL") # Your Railway Proxy
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE = os.getenv("AIRTABLE_BASE")
AIRTABLE_TABLE = os.getenv("AIRTABLE_TABLE", "Contacts")

# Initialize Airtable
airtable_api = Api(AIRTABLE_TOKEN)
table = airtable_api.table(AIRTABLE_BASE, AIRTABLE_TABLE)

SCRAPE_PROMPT = """Extract contact info from this QuickBooks screenshot. 
Return ONLY valid JSON, no markdown:
{"company":"","first_name":"","last_name":"","email":"","company_phone":"","city":"","state":"","products":"","customer_type":"","customer_lifetime":"","company_id":"","confidence":"high|medium|low"}"""

@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    filename = file.filename

    try:
        # 1. Encode Image
        b64 = base64.b64encode(file.read()).decode()

        # 2. Call your Proxy
        payload = {
            "model": "gpt-5-chat-latest",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}},
                        {"type": "text", "text": SCRAPE_PROMPT}
                    ]
                }
            ],
            "response_format": {"type": "json_object"}
        }

        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        resp = requests.post(PROXY_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        
        # 3. Parse and add Metadata
        clean_data = resp.json()["choices"][0]["message"]["content"]
        data_dict = json.loads(clean_data)
        data_dict["Source_File"] = filename

        # 4. Send to Airtable
        table.create(data_dict)

        return jsonify({"status": "success", "file": filename})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
