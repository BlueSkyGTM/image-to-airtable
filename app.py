import os
import json
import base64
import requests
from flask import Flask, request, jsonify
from pyairtable import Api

app = Flask(__name__)

# --- CONFIG ---
# Using your private internal address
PROXY_URL = "http://openai-proxy.railway.internal/v1/chat/completions" 
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE = os.getenv("AIRTABLE_BASE")
AIRTABLE_TABLE = os.getenv("AIRTABLE_TABLE", "Contacts")

airtable_api = Api(AIRTABLE_TOKEN)
table = airtable_api.table(AIRTABLE_BASE, AIRTABLE_TABLE)

# Updated prompt with exact Airtable column names
SCRAPE_PROMPT = """Extract contact info from this QuickBooks screenshot. 
Return ONLY valid JSON, no markdown. Use these EXACT keys:
{"Company":"","First Name":"","Last Name":"","Email":"","Direct Phone":"","City":"","State":"","Products":"","Customer Type":"","Customer Lifetime":""}"""

@app.route('/process', methods=['POST'])
def process():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file"}), 400

    try:
        b64 = base64.b64encode(file.read()).decode()
        
        payload = {
            "model": "gpt-4o", # Using gpt-4o via your proxy
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

        # Sending to your "Not your grandmother's proxy"
        resp = requests.post(PROXY_URL, json=payload, timeout=60)
        resp.raise_for_status()
        
        # Parse result and send to Airtable
        gpt_data = json.loads(resp.json()["choices"][0]["message"]["content"])
        table.create(gpt_data)

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
