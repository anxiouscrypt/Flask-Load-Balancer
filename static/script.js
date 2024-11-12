let isLoggedIn = false;
const adminCredentials = { username: "admin", password: "admin" }; // Simple admin check for demo

// Login Function
function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    if (username === adminCredentials.username && password === adminCredentials.password) {
        isLoggedIn = true;
        document.getElementById("login-container").style.display = "none";
        document.getElementById("dashboard-container").style.display = "block";
        fetchStats();
        startHealthCheck();
    } else {
        document.getElementById("login-error").textContent = "Invalid credentials";
    }
}

// Fetch Server Stats
async function fetchStats() {
    try {
        const response = await fetch("http://127.0.0.1:5006/stats");
        const data = await response.json();
        displayServerStats(data);
    } catch (error) {
        console.error("Error fetching stats:", error);
        alert("Error fetching stats");
    }
}

// Display Server Stats
function displayServerStats(data) {
    const serverList = document.getElementById("server-list");
    serverList.innerHTML = '';  // Clear previous list

    // Iterate through the servers and update their status
    Object.keys(data.servers).forEach(server => {
        const statusClass = data.servers[server].status === "healthy" ? "healthy" : "down";
        const serverDiv = document.createElement("div");
        serverDiv.classList.add(statusClass);
        serverDiv.innerHTML = `${server}: ${data.servers[server].status}`;
        serverList.appendChild(serverDiv);
    });

    const totalRequests = document.getElementById("stats-container");
    totalRequests.innerHTML = `<p>Total Requests: ${data.total_requests}</p>`;
}

// Add Server
async function addServer() {
    const url = document.getElementById("new-server-url").value;
    if (url) {
        try {
            const response = await fetch("http://127.0.0.1:5006/add_server", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ url })
            });
            const result = await response.json();
            if (response.ok) {
                alert(result.message);
                fetchStats();  // Refresh stats
            } else {
                alert(result.error);
            }
        } catch (error) {
            console.error("Error adding server:", error);
            alert("Error adding server");
        }
    }
}

// Remove Server
async function removeServer() {
    const url = document.getElementById("new-server-url").value;
    if (url) {
        try {
            const response = await fetch("http://127.0.0.1:5006/remove_server", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ url })
            });
            const result = await response.json();
            if (response.ok) {
                alert(result.message);
                fetchStats();  // Refresh stats
            } else {
                alert(result.error);
            }
        } catch (error) {
            console.error("Error removing server:", error);
            alert("Error removing server");
        }
    }
}

// Refresh Stats
function refreshStats() {
    fetchStats();
}

// Real-time Health Check (polling every 10 seconds)
function startHealthCheck() {
    setInterval(() => {
        fetchStats();  // Fetch and update server health every 10 seconds
    }, 10000);  // Update every 10 seconds
}
