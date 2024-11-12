from flask import Flask, request, jsonify
import requests
import threading
import time
import hashlib

app = Flask(__name__)

# Initial list of backend servers
backend_servers_init = [
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002",
    "http://127.0.0.1:5003"
]

# Active and down servers
backend_servers = []
backend_servers_down = []
lock = threading.Lock()

def check_health_status(server):
    try:
        response = requests.get(server + "/health", timeout=3)
        return response.json().get("status") == "healthy"
    except requests.exceptions.RequestException:
        return False

def init_servers():
    """Initialize the servers with their initial health status."""
    for server in backend_servers_init:
        if check_health_status(server):
            backend_servers.append(server)

def continuous_health_check():
    """Continuously check server health and update status."""
    while True:
        time.sleep(10)  # Health check interval
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

def get_server_by_ip_hash(client_ip):
    """Get server based on IP hashing."""
    if not backend_servers:
        return None
    # Generate a hash of the client's IP address
    ip_hash = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
    # Map the hash to an index in the backend_servers list
    server_index = ip_hash % len(backend_servers)
    return backend_servers[server_index]

@app.route('/')
def load_balancer():
    client_ip = request.remote_addr  # Get the client's IP address
    with lock:
        server = get_server_by_ip_hash(client_ip)

    if server:
        try:
            response = requests.get(server, timeout=3)
            return jsonify(response.json())
        except requests.exceptions.RequestException:
            with lock:
                if server in backend_servers:
                    backend_servers.remove(server)
                    backend_servers_down.append(server)
            return jsonify({"error": "Server is currently unavailable"}), 503

    return jsonify({"error": "No backend servers available"}), 503

@app.route('/list_servers', methods=['GET'])
def list_servers():
    with lock:
        return jsonify({"servers up": backend_servers})
    
@app.route('/list_servers_down', methods=['GET'])
def list_servers_down():
    with lock:
        return jsonify({"servers down": backend_servers_down})


# Server management endpoints remain the same (e.g., /add_server, /remove_server)

if __name__ == '__main__':
    init_servers()
    threading.Thread(target=continuous_health_check, daemon=True).start()
    app.run(port=5005)
