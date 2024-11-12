from flask import Flask, request, jsonify
import requests
import threading
import time

app = Flask(__name__)

backend_servers_init = [
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002",
    "http://127.0.0.1:5003"
]

backend_servers = []
backend_servers_down = []
current_server_index = 0
lock = threading.Lock()

def check_health_status(server):
    try:
        response = requests.get(server + "/health", timeout=3)
        return response.json().get("status") == "healthy"
    except requests.exceptions.RequestException:
        return False

def init_servers():
    """Initialize the healthy servers list."""
    for server in backend_servers_init:
        if check_health_status(server):
            backend_servers.append(server)

def continuous_health_check():
    """Run health checks on servers at regular intervals."""
    while True:
        time.sleep(10)  # Check every 10 seconds
        with lock:
            for server in backend_servers[:]:
                if not check_health_status(server):
                    backend_servers.remove(server)
                    backend_servers_down.append(server)
                    print(f"Server {server} is down, removed from active list.")
            for server in backend_servers_down[:]:
                if check_health_status(server):
                    backend_servers_down.remove(server)
                    backend_servers.append(server)
                    print(f"Server {server} is back online, added to active list.")

@app.route('/')
def load_balancer():
    global current_server_index

    if not backend_servers:
        return jsonify({"error": "No backend servers available"}), 503

    attempts = 0
    while attempts < len(backend_servers):
        with lock:
            server = backend_servers[current_server_index]
            current_server_index = (current_server_index + 1) % len(backend_servers)

        try:
            if check_health_status(server):
                response = requests.get(server, timeout=3)
                return jsonify(response.json())
            else:
                with lock:
                    backend_servers.remove(server)
                    backend_servers_down.append(server)
            attempts += 1
        except requests.exceptions.RequestException:
            with lock:
                backend_servers.remove(server)
                backend_servers_down.append(server)
            attempts += 1

    return jsonify({"error": "All backend servers are down"}), 503

@app.route('/add_server', methods=['POST'])
def add_server():
    server_url = request.json.get("url")
    with lock:
        if server_url and server_url not in backend_servers:
            backend_servers.append(server_url)
            return jsonify({"message": "Server added", "servers": backend_servers}), 201
    return jsonify({"error": "Server URL is missing or already exists"}), 400

@app.route('/remove_server', methods=['POST'])
def remove_server():
    server_url = request.json.get("url")
    with lock:
        if server_url in backend_servers:
            backend_servers.remove(server_url)
            return jsonify({"message": "Server removed", "servers": backend_servers}), 200
    return jsonify({"error": "Server URL not found"}), 404

@app.route('/list_servers', methods=['GET'])
def list_servers():
    with lock:
        return jsonify({"servers up": backend_servers})
    
@app.route('/list_servers_down', methods=['GET'])
def list_servers_down():
    with lock:
        return jsonify({"servers down": backend_servers_down})

if __name__ == '__main__':
    init_servers()
    threading.Thread(target=continuous_health_check, daemon=True).start()
    app.run(port=5000)
