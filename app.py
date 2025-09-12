from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # allow all origins for simplicity

# Configure upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route('/ModelThree/api', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    return jsonify({"status": "success", "message": f"File {filename} uploaded successfully"})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5003)
