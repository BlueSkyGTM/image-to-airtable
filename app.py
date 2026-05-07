import os
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from pyairtable import Api

# 1. Setup the Web Server
app = Flask(__name__)

# 2. Setup the "Lockbox" (Environment Variables)
# These names must match EXACTLY what you type into the Railway Variables tab
AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN')
BASE_ID = os.environ.get('BASE_ID')
TABLE_NAME = os.environ.get('TABLE_NAME', 'Images') # It will use 'Images' by default

# 3. Connect to Airtable
api = Api(AIRTABLE_TOKEN)
table = api.table(BASE_ID, TABLE_NAME)

@app.route('/scrape', methods=['GET'])
def scrape():
    # Grab the URL from the request
    target_url = request.args.get('url')
    
    if not target_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # Visit the website
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(target_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all images
        image_links = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # If the link is relative (like "/logo.png"), this makes it a full URL
                if src.startswith('/'):
                    from urllib.parse import urljoin
                    src = urljoin(target_url, src)
                image_links.append(src)

        # 4. Send each image link to Airtable
        # Note: Your Airtable table needs a column named "URL" and "Image Link"
        for link in image_links:
            table.create({
                "URL": target_url,
                "Image Link": link
            })

        return jsonify({
            "status": "Success", 
            "message": f"Found {len(image_links)} images and sent them to Airtable."
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 5. Start the Engine
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
