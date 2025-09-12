from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
 
@app.route('/api', methods=['POST'])
def handle_post():
    return jsonify({"status": "success", "message": "POST request received"})

@app.route('/api', methods=['GET'])
def handle_get():
    return jsonify({"status": "success", "message": "GET request received"})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5003)
