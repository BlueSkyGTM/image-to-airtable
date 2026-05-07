from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

# This line initializes your web server
app = Flask(__name__)

# This defines the "address" where people can find your scraper
@app.route('/scrape', methods=['GET'])
def scrape():
    # 1. Grab the URL from the request (e.g., /scrape?url=https://example.com)
    target_url = request.args.get('url')
    
    if not target_url:
        return jsonify({"error": "You forgot to provide a URL!"}), 400

    try:
        # 2. Visit the website
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(target_url, headers=headers, timeout=10)
        
        # 3. Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 4. Find all image tags (<img>) and grab their 'src' (the link)
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                images.append(src)

        # 5. Send the list of image links back to whoever asked
        return jsonify({"images": images})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# This part tells the app how to run on Railway
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)