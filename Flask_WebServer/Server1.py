from flask import Flask, jsonify, request
import time
import logging

app = Flask(__name__)

status = "healthy"

@app.route('/')

def index():
    return jsonify({"server": "Server 1", "message": "Hello from Server 1!"})
    

@app.route('/status')
def health_check():
    return jsonify({"status": status})

logging.basicConfig(
    level=logging.INFO,  # Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Define log format
    handlers=[ 
        logging.StreamHandler()  # Print logs to console
    ]
)

@app.route('/set_health', methods=[ 'POST'])
def set_health():
    global status
    status = request.json.get('status')
    return jsonify({"message": "Health Updated", "Status": status}), 201

if __name__ == '__main__':
    app.run(port=5001)  # Run Server 1 on port 5001