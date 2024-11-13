from flask import Flask, request, jsonify, send_from_directory
import requests
import threading
import time
from Servers import Server
from globals import *

lock =threading.Lock()

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
            if server.get_status() == "healthy":
                response = requests.get(server.ip, timeout=3)
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