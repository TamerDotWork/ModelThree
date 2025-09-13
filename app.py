from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api', methods=['POST'])
def api():
    data = request.get_json()  # receive JSON from AJAX
    print("Received:", data)   # print to terminal
    return jsonify({"message": "Hello, World!"})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5003)
