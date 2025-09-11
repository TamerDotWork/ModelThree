from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Store logs in memory for demonstration
logs = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api', methods=['GET', 'POST'])
def api():
    if request.method == 'POST':
        data = request.json  # expecting JSON payload
        logs.append(data)
        print(f"Received POST data: {data}")  # log to console
        return jsonify({"status": "success", "data_received": data})
    
    # GET request: return logs
    return jsonify({"status": "success", "logs": logs})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
