Tkinter WebSocket + HTTP Client

A lightweight Python 3 desktop client built with tkinter for testing and interacting with servers via WebSocket and HTTP.

This tool is designed for developers who need a simple UI to send JSON-based commands, debug APIs, and monitor responses in real time.

✨ Features
🧩 User-friendly GUI (Tkinter)
⚡ WebSocket support
Connect / Disconnect
Send JSON messages
Real-time response logging
🌐 HTTP client
Send customizable HTTP requests (method, headers, body)
📋 Command input
Paste or edit JSON commands easily
🎯 Quick presets
5 selectable default commands for fast testing
🪵 Live logging panel
Displays connection status, requests, responses, and errors
🧵 Non-blocking UI
WebSocket and HTTP run in background threads
✅ JSON validation before sending
🗂 Project Structure
tk_ws_http_client/
├── main.py              # Main application
├── requirements.txt    # Python dependencies
├── README.md           # Documentation
├── default_commands.json
⚙️ Requirements
Python 3.10+ (recommended)
tkinter (usually included with Python)

On Linux, you may need:

sudo apt install python3-tk
📦 Installation
1. Clone or download the project
git clone <your-repo-url>
cd tk_ws_http_client
2. Create a virtual environment
Windows
python -m venv .venv
.venv\Scripts\activate
macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
▶️ Run the Application
Windows
python main.py
macOS / Linux
python3 main.py
🧪 Usage
🔌 WebSocket

Enter your WebSocket URL
Example:

ws://localhost:8765/ws
Click Connect
Paste a JSON command into the Command / Request box
Click Send
View responses in the Logs panel
Click Disconnect when done
Example JSON
{
  "action": "ping",
  "timestamp": "2026-03-27T12:00:00Z"
}
🌐 HTTP Requests

Enter your base URL
Example:

http://localhost:8000
Use the following JSON format:
{
  "method": "POST",
  "path": "/api/commands",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "action": "status"
  },
  "timeout": 10
}
Click Send HTTP
View status code and response in Logs
🎯 Default Commands
Use the 5 checkboxes at the top to quickly load predefined commands
Selecting an option will automatically populate the request textbox
You can modify the JSON after loading
📝 Notes
Add authentication headers (e.g., tokens) via the headers field
HTTP requests currently send data using json=body
You can extend the tool to support:
Raw request body
Query parameters
Authentication flows
Request history
Save/load configurations
🛠 Tech Stack
Python 3
Tkinter (GUI)
websocket-client
requests
🤝 Contributing

Feel free to fork this project and submit pull requests. Suggestions and improvements are welcome!

📄 License

This project is provided for educational and development purposes. You may adapt it freely for your own use.