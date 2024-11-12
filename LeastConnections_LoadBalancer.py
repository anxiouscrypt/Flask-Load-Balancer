from flask import Flask, request, jsonify, send_from_directory
import requests
import threading
import time

app = Flask(__name__)

# Initial list of backend servers
backend_servers_init = [
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002",
    "http://127.0.0.1:5003",
]

# Active servers and connection counts
backend_servers = []
backend_servers_down = []
current_server_index = 0
connection_counts = {}
lock = threading.Lock()

# Request count for stats
request_count = 0

# Serve dashboard (frontend)
@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory('static', 'index.html')

def check_health_status(server):
    """Check the health status of a server."""
    try:
        response = requests.get(server + "/health", timeout=3)
        return response.json().get("status") == "healthy"
    except requests.exceptions.RequestException:
        return False

def init_servers():
    """Initialize the servers with their initial health status and connection count."""
    for server in backend_servers_init:
        if check_health_status(server):
            backend_servers.append(server)
            connection_counts[server] = 0  # Initialize connection count
            print(f"Server {server} is online, added to active list.")
        else:
            backend_servers_down.append(server)
            print(f"Server {server} is down, notadded to active list.")

def continuous_health_check():
    """Continuously check server health and update status."""
    while True:
        time.sleep(10)  # Health check interval
        with lock:
            # Check each server's health and update the lists
            for server in backend_servers[:]:
                if not check_health_status(server):
                    backend_servers.remove(server)
                    backend_servers_down.append(server)
                    connection_counts.pop(server, None)  # Remove from connection count
                    print(f"Server {server} is down, removed from active list.")
            for server in backend_servers_down[:]:
                if check_health_status(server):
                    backend_servers_down.remove(server)
                    backend_servers.append(server)
                    connection_counts[server] = 0  # Reset connection count for healthy server
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

@app.route('/stats')
def get_stats():
    """Route to fetch server statistics."""
    try:
        stats = server_stats()
        return jsonify({
            "total_requests": request_count,
            "servers": stats
        })
    except Exception as e:
        return jsonify({"error": "Failed to retrieve stats"}), 500

@app.route('/add_server', methods=['POST'])
def add_server():
    """Route to add a new backend server."""
    server_url = request.json.get("url")
    with lock:
        if server_url and server_url not in backend_servers:
            backend_servers.append(server_url)
            return jsonify({"message": "Server added", "servers": backend_servers}), 201
    return jsonify({"error": "Server URL is missing or already exists"}), 400

@app.route('/remove_server', methods=['POST'])
def remove_server():
    """Route to remove a backend server."""
    server_url = request.json.get("url")
    with lock:
        if server_url in backend_servers:
            backend_servers.remove(server_url)
            return jsonify({"message": "Server removed", "servers": backend_servers}), 200
    return jsonify({"error": "Server URL not found"}), 404

@app.route('/list_servers', methods=['GET'])
def list_servers():
    """Route to list all active backend servers."""
    with lock:
        return jsonify({"servers up": backend_servers})

@app.route('/list_servers_down', methods=['GET'])
def list_servers_down():
    """Route to list all down backend servers."""
    with lock:
        return jsonify({"servers down": backend_servers_down})

def get_server_status(server_url):
    """Perform a health check on a given server."""
    try:
        response = requests.get(server_url + "/health", timeout=3)
        if response.status_code == 200:
            return response.json().get("status", "unknown")
        else:
            return "unhealthy"
    except requests.exceptions.RequestException:
        return "unreachable"

def server_stats():
    """Return the health status of all backend servers."""
    stats = {}
    for server in backend_servers_init:
        stats[server] = {
            "requests_handled": connection_counts.get(server, 0),
            "status": get_server_status(server)
        }
    return stats

if __name__ == '__main__':
    init_servers()
    threading.Thread(target=continuous_health_check, daemon=True).start()
    app.run(port=5006)
