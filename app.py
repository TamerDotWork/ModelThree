from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
 
@app.route('/ModelThree/api', methods=['POST'])
def api():
    data = request.get_json(silent=True)  # optional input
    print("Received:", data)
    return jsonify({"message": "Hello, World!"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5003, debug=True)
