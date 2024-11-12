from flask import Flask, jsonify, request
import time
import logging

app = Flask(__name__)

health_status = "healthy"

@app.route('/')

def index():
    return jsonify({"server": "Server 3", "message": "Hello from Server 3!"})
    

@app.route('/health')
def health_check():
    return jsonify({"status": health_status})

logging.basicConfig(
    level=logging.INFO,  # Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Define log format
    handlers=[ 
        logging.StreamHandler()  # Print logs to console
    ]
)

@app.route('/set_health', methods=[ 'POST'])
def set_health():
    global health_status
    health_status = request.json.get('health')
    return jsonify({"message": "Health Updated", "Status": health_status}), 201

if __name__ == '__main__':
    app.run(port=5003)  # Run Server 1 on port 5001