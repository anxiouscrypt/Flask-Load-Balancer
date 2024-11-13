import requests

class Server:

    def __init__(self, ip, connection_counts=None):
        self.ip = ip
        self.status = self.get_status()
        if connection_counts is not None:
            self.set_connection_counts(connection_counts)
        else:
            self.set_connection_counts(0)
        
    def get_ip(self):
        return self.ip
    
    def set_ip(self, ip):
        self.ip = ip

    def get_status(self):
        """Dynamically fetch the server's status by calling the /status endpoint."""
        try:
            response = requests.get(self.ip + "/status", timeout=3)
            if response.status_code == 200:
                current_status = response.json().get("status")
                return current_status
            else:
                return f"Error: Received status code {response.status_code}"
        except requests.exceptions.RequestException as e:
            return f"Error: {e}"

    def set_status(self, status):
        """Set the status of the server by sending a POST request."""
        data = {"status": status}  # Replace with the actual data you want to send
        headers = {'Content-Type': 'application/json'}
        
        try:
            # POST request to set the status
            response = requests.post(self.ip + "/set_health", json=data, headers=headers)
            if response.status_code == 201:
                return "Request was successful:", response.json()
            else:
                return f"Request failed with status code {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Error in setting status: {e}"

    def get_connection_counts(self):
        return self.connection_counts
    
    def set_connection_counts(self, connection_count):
        self.connection_counts = connection_count
    
    def to_dict(self):
        return {
            "ip": self.ip,
            "status": self.status,
            "connection_counts": self.connection_counts
        }