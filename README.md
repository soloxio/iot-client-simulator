# 🚀 Tkinter WebSocket + HTTP Client

A lightweight Python 3 desktop client built with `tkinter` for testing
and interacting with servers via **WebSocket** and **HTTP**.

This tool is designed for developers who need a simple UI to send
JSON-based commands, debug APIs, and monitor responses in real time.

------------------------------------------------------------------------

## ✨ Features

-   🧩 **User-friendly GUI (Tkinter)**
-   ⚡ **WebSocket support**
    -   Connect / Disconnect
    -   Send JSON messages
    -   Real-time response logging
-   🌐 **HTTP client**
    -   Send customizable HTTP requests (method, headers, body)
-   📋 **Command input**
    -   Paste or edit JSON commands easily
-   🎯 **Quick presets**
    -   5 selectable default commands for fast testing
-   🪵 **Live logging panel**
    -   Displays connection status, requests, responses, and errors
-   🧵 **Non-blocking UI**
    -   WebSocket and HTTP run in background threads
-   ✅ **JSON validation before sending**

------------------------------------------------------------------------

## 🗂 Project Structure

	tk_ws_http_client_refactored/
	├── main.py
	├── ui.py
	├── ws_client.py
	├── http_client.py
	├── utilities.py
	├── requirements.txt
	└── README.md

------------------------------------------------------------------------

## ⚙️ Requirements

-   Python **3.10+**
-   tkinter (included with Python, Linux may need python3-tk)

------------------------------------------------------------------------

## 📦 Installation

``` bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

------------------------------------------------------------------------

## ▶️ Run

``` bash
python main.py
```

------------------------------------------------------------------------

## 🧪 Usage

### WebSocket

-   Enter URL: ws://localhost:8765/ws
-   Click Connect → Send → Disconnect

Example:

``` json
{
  "action": "ping",
  "timestamp": "2026-03-27T12:00:00Z"
}
```

### HTTP

``` json
{
  "method": "POST",
  "path": "/api/commands",
  "headers": {"Content-Type": "application/json"},
  "body": {"action": "status"},
  "timeout": 10
}
```

------------------------------------------------------------------------

## 🛠 Tech Stack

-   Python
-   Tkinter
-   requests
-   websocket-client

------------------------------------------------------------------------

## 📄 License

Free to use and modify.

------------------------------------------------------------------------

## 🔔 Confluence Notification API – Comparison & Mismatches

This section documents the relevant Confluence Notification REST API
specification and how the current implementation aligns (or does not
align) with it.

### Confluence Notification API – Key Endpoints

| Method   | Endpoint                                                       | Purpose                    |
|----------|----------------------------------------------------------------|----------------------------|
| `GET`    | `/rest/mywork/latest/status/notification/count`                | Get unread notification count |
| `GET`    | `/rest/notifications/latest/notification`                      | List notifications         |
| `POST`   | `/rest/notifications/latest/notification`                      | Create a notification      |
| `DELETE` | `/rest/notifications/latest/notification/{id}`                 | Delete a notification      |
| `PUT`    | `/rest/notifications/latest/notification/{id}/read`            | Mark notification as read  |

### Notification Object Schema (POST body)

``` json
{
  "userKey":     "target-user-key",
  "title":       "Notification title",
  "description": "Notification body / description",
  "iconUrl":     "https://example.com/icon.png",
  "itemUrl":     "https://example.com/item",
  "itemId":      "unique-item-id"
}
```

`userKey` is required; all other fields are optional but recommended.

### Authentication

All notification endpoints require authentication via an
`Authorization` header:

``` http
Authorization: Basic REPLACE_WITH_YOUR_CREDENTIALS
```

OAuth tokens are also supported.

### Current Implementation vs. Confluence Notification API

| # | Requirement                                      | Status | Notes |
|---|--------------------------------------------------|--------|-------|
| 1 | HTTP `POST /rest/notifications/latest/notification` preset | ✅ Fixed | **"Create Notification"** default command now targets the correct path and includes required body fields (`userKey`, `title`, `description`, `iconUrl`, `itemUrl`, `itemId`). |
| 2 | `Authorization` header in HTTP presets           | ✅ Fixed | **"Create Notification"** preset now includes `Authorization: Basic` header. |
| 3 | WebSocket subscribe to `notifications` channel   | ✅ Fixed | **"Subscribe"** command now uses `"channel": "notifications"` instead of the former generic `"channel": "events"`. |
| 4 | HTTP `GET /rest/notifications/latest/notification` preset | ❌ Missing | No default command for listing notifications. Use the HTTP base URL + manual JSON to call this endpoint. |
| 5 | HTTP `GET /rest/mywork/latest/status/notification/count` preset | ❌ Missing | No default command for reading the unread-count endpoint. |
| 6 | HTTP `DELETE /rest/notifications/latest/notification/{id}` preset | ❌ Missing | No default command for deleting a notification. |
| 7 | HTTP `PUT /rest/notifications/latest/notification/{id}/read` preset | ❌ Missing | No default command for marking a notification as read. |

### Remaining Mismatches

Items 4 – 7 in the table above are not covered by a one-click default
command.  You can still exercise all of these endpoints manually by
entering the appropriate JSON in the **Command / Request** text box.

Examples:

**List notifications**

``` json
{
  "method": "GET",
  "path": "/rest/notifications/latest/notification",
  "headers": { "Authorization": "Basic REPLACE_WITH_YOUR_CREDENTIALS" },
  "timeout": 10
}
```

**Get unread notification count**

``` json
{
  "method": "GET",
  "path": "/rest/mywork/latest/status/notification/count",
  "headers": { "Authorization": "Basic REPLACE_WITH_YOUR_CREDENTIALS" },
  "timeout": 10
}
```

**Delete notification**

``` json
{
  "method": "DELETE",
  "path": "/rest/notifications/latest/notification/{id}",
  "headers": { "Authorization": "Basic REPLACE_WITH_YOUR_CREDENTIALS" },
  "timeout": 10
}
```

**Mark notification as read**

``` json
{
  "method": "PUT",
  "path": "/rest/notifications/latest/notification/{id}/read",
  "headers": { "Authorization": "Basic REPLACE_WITH_YOUR_CREDENTIALS" },
  "timeout": 10
}
```
