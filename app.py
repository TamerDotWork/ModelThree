from flask import Flask, request, jsonify ,render_template
from flask_cors import CORS

app = Flask(__name__)


# Store logs in memory for demonstration
logs = []

@app.route('/')
def index():
    return render_template('index.html')

 
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5003)
