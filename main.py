from flask import Flask, request, jsonify, send_from_directory
import threading
import time
from Servers import Server
from LoadBalancer import load_balancer
from globals import *
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
lock = threading.Lock()

# Request count for stats
request_count = 0

# Serve dashboard (frontend)
@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory('static', 'index.html')

def init_servers():
    for IP in server_IPs:
        server = Server(IP, connection_counts=0)
        if server.get_status() == "healthy":
            backend_servers.append(server)
            print(f"Server {server.ip} is online, added to active list.")
        else:
            backend_servers_down.append(server)
            print(f"Server {server.ip} is down, not added to active list.")

def continuous_health_check():
    """Continuously check server health and update status."""
    while True:
        time.sleep(10)  # Health check interval
        with lock:
            # Check each server's health and update the lists
            for server in backend_servers[:]:
                if not server.check_health_status():
                    backend_servers.remove(server)
                    backend_servers_down.append(server)
                    server.connection_counts -= 1  # Remove from connection count
                    print(f"Server {server.ip} is down, removed from active list.")
            for server in backend_servers_down[:]:
                if server.check_health_status():
                    backend_servers_down.remove(server)
                    backend_servers.append(server)
                    server.connection_counts = 0  # Reset connection count for healthy server
                    print(f"Server {server.ip} is back online, added to active list.")

@app.route('/')
def route_load_balancer():
    return load_balancer()

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
    
    if not server_url:
        return jsonify({"error": "Server URL is missing"}), 400
    
    # Check if the server is already in either list
    with lock:
        # If the server URL is already in the active or down server list, do not add
        if any(server.get_ip() == server_url for server in backend_servers) or \
           any(server.get_ip() == server_url for server in backend_servers_down):
            return jsonify({"error": "Server already exists"}), 400
        
        # If the server is not in the lists, add it to backend_servers (healthy by default)
        new_server = Server(server_url, connection_counts=0)
        backend_servers.append(new_server)
        
        # Return updated list of all servers (active and down)
        all_servers = backend_servers + backend_servers_down
        return jsonify({"message": "Server added", "servers": [server.get_ip() for server in all_servers]}), 201

@app.route('/remove_server', methods=['POST'])
def remove_server():
    """Route to remove a backend server."""
    server_url = request.json.get("url")
    with lock:
        if server_url in backend_servers:
            backend_servers.remove(server_url)
            return jsonify({"message": "Server removed", "servers": backend_servers}), 200
    return jsonify({"error": "Server URL not found"}), 404

def server_stats():
    """Return the health status and request counts of all backend servers, both active and down."""
    stats = {}
    
    # Combine both backend_servers and backend_servers_down to include all servers
    all_servers = backend_servers + backend_servers_down

    # Iterate over all server instances
    for server in all_servers:
        stats[server.get_ip()] = {  # Using server's IP for the key
            "requests_handled": server.connection_counts,  # Access connection_counts
            "status": server.get_status()  # Get the status of the server
        }
    
    return stats

if __name__ == '__main__':
    init_servers()
    threading.Thread(target=continuous_health_check, daemon=True).start()
    app.run(port=5006)
