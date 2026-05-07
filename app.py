import os
from flask import Flask, request, jsonify
from pyairtable import Api

app = Flask(__name__)

# Airtable Config (Keep these in your Railway Variables!)
AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN')
BASE_ID = os.environ.get('BASE_ID')
TABLE_NAME = os.environ.get('TABLE_NAME', 'Images')

api = Api(AIRTABLE_TOKEN)
table = api.table(BASE_ID, TABLE_NAME)

@app.route('/upload', methods=['POST'])
def upload_image():
    # Check if a file was actually sent
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Note: Airtable requires a public URL to "attach" an image.
        # If you are sending raw bytes, you usually need a middle-man like Cloudinary.
        # For now, let's just send the Filename to prove the connection works.
        
        table.create({
            "URL": "Local Upload",
            "Image Link": file.filename
        })

        return jsonify({"status": "Success", "filename": file.filename})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
