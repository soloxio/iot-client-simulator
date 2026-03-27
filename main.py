import json
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime

import requests
from websocket import WebSocketApp


DEFAULT_COMMANDS = [
    {
        "name": "Ping",
        "payload": {
            "action": "ping",
            "timestamp": "2026-03-27T12:00:00Z"
        }
    },
    {
        "name": "Login",
        "payload": {
            "action": "login",
            "username": "demo_user",
            "token": "replace-me"
        }
    },
    {
        "name": "Subscribe",
        "payload": {
            "action": "subscribe",
            "channel": "events"
        }
    },
    {
        "name": "Echo",
        "payload": {
            "action": "echo",
            "message": "hello from tkinter client"
        }
    },
    {
        "name": "HTTP POST sample",
        "payload": {
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
    }
]


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Tkinter WebSocket + HTTP Client")
        self.root.geometry("980x760")
        self.root.minsize(900, 680)

        self.ws_app = None
        self.ws_thread = None
        self.ws_connected = False
        self.selected_option = tk.IntVar(value=0)

        self._build_ui()
        self._set_default_text()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(5, weight=1)

        title = ttk.Label(
            self.root,
            text="Python 3 Tkinter Client - WebSocket + HTTP",
            font=("Segoe UI", 15, "bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

        options_frame = ttk.LabelFrame(self.root, text="Default commands")
        options_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=6)
        options_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.option_buttons = []
        for i, command in enumerate(DEFAULT_COMMANDS, start=1):
            btn = ttk.Checkbutton(
                options_frame,
                text=command["name"],
                variable=self.selected_option,
                onvalue=i,
                offvalue=0,
                command=self._on_option_toggle,
            )
            btn.grid(row=0, column=i - 1, sticky="w", padx=8, pady=8)
            self.option_buttons.append(btn)

        server_frame = ttk.LabelFrame(self.root, text="Server configuration")
        server_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=6)
        server_frame.columnconfigure(1, weight=1)

        ttk.Label(server_frame, text="WebSocket URL:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.ws_url_var = tk.StringVar(value="ws://localhost:8765/ws")
        ttk.Entry(server_frame, textvariable=self.ws_url_var).grid(row=0, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(server_frame, text="HTTP Base URL:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.http_url_var = tk.StringVar(value="http://localhost:8000")
        ttk.Entry(server_frame, textvariable=self.http_url_var).grid(row=1, column=1, sticky="ew", padx=8, pady=6)

        request_frame = ttk.LabelFrame(self.root, text="Command / Request")
        request_frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=6)
        request_frame.columnconfigure(1, weight=1)
        request_frame.rowconfigure(0, weight=1)

        req_label = (
            "Paste JSON command for WebSocket, or HTTP request JSON.\n"
            "HTTP JSON format example: {\"method\":\"POST\",\"path\":\"/api/demo\",\"headers\":{},\"body\":{...}}"
        )
        ttk.Label(request_frame, text=req_label, justify="left").grid(
            row=0, column=0, sticky="nw", padx=8, pady=8
        )

        self.request_text = ScrolledText(request_frame, wrap="word", height=16)
        self.request_text.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=4, column=0, sticky="ew", padx=12, pady=6)
        for idx in range(4):
            button_frame.columnconfigure(idx, weight=1)

        ttk.Button(button_frame, text="Connect", command=self.connect).grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        ttk.Button(button_frame, text="Disconnect", command=self.disconnect).grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(button_frame, text="Send", command=self.send_websocket).grid(row=0, column=2, sticky="ew", padx=6, pady=6)
        ttk.Button(button_frame, text="Send HTTP", command=self.send_http).grid(row=0, column=3, sticky="ew", padx=6, pady=6)

        log_frame = ttk.LabelFrame(self.root, text="Logs")
        log_frame.grid(row=5, column=0, sticky="nsew", padx=12, pady=(6, 12))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = ScrolledText(log_frame, wrap="word", height=14, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    def _set_default_text(self) -> None:
        self.request_text.delete("1.0", tk.END)
        self.request_text.insert("1.0", json.dumps(DEFAULT_COMMANDS[0]["payload"], indent=2))

    def _on_option_toggle(self) -> None:
        selected = self.selected_option.get()
        if selected == 0:
            self._log("Default command selection cleared.")
            return

        payload = DEFAULT_COMMANDS[selected - 1]["payload"]
        self.request_text.delete("1.0", tk.END)
        self.request_text.insert("1.0", json.dumps(payload, indent=2))
        self._log(f'Loaded default command: {DEFAULT_COMMANDS[selected - 1]["name"]}')

    def _log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"

        def append() -> None:
            self.log_text.configure(state="normal")
            self.log_text.insert(tk.END, full_message)
            self.log_text.see(tk.END)
            self.log_text.configure(state="disabled")

        self.root.after(0, append)

    def _get_request_text(self) -> str:
        return self.request_text.get("1.0", tk.END).strip()

    def connect(self) -> None:
        if self.ws_connected:
            self._log("WebSocket is already connected.")
            return

        ws_url = self.ws_url_var.get().strip()
        if not ws_url:
            self._log("WebSocket URL is empty.")
            return

        self._log(f"Connecting to WebSocket: {ws_url}")

        def run_ws() -> None:
            self.ws_app = WebSocketApp(
                ws_url,
                on_open=self._on_ws_open,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close,
            )
            try:
                self.ws_app.run_forever()
            except Exception as exc:
                self._log(f"WebSocket run_forever exception: {exc}")

        self.ws_thread = threading.Thread(target=run_ws, daemon=True)
        self.ws_thread.start()

    def disconnect(self) -> None:
        if self.ws_app is None:
            self._log("No active WebSocket connection.")
            return

        self._log("Disconnecting WebSocket...")
        try:
            self.ws_app.close()
        except Exception as exc:
            self._log(f"Disconnect error: {exc}")

    def send_websocket(self) -> None:
        if not self.ws_connected or self.ws_app is None:
            self._log("Cannot send via WebSocket: not connected.")
            return

        raw_text = self._get_request_text()
        if not raw_text:
            self._log("Request textbox is empty.")
            return

        try:
            parsed = json.loads(raw_text)
            payload = json.dumps(parsed)
        except json.JSONDecodeError as exc:
            self._log(f"Invalid JSON for WebSocket send: {exc}")
            return

        try:
            self.ws_app.send(payload)
            self._log(f"Sent WebSocket message: {payload}")
        except Exception as exc:
            self._log(f"WebSocket send error: {exc}")

    def send_http(self) -> None:
        raw_text = self._get_request_text()
        if not raw_text:
            self._log("Request textbox is empty.")
            return

        try:
            request_data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            self._log(f"Invalid JSON for HTTP request: {exc}")
            return

        method = str(request_data.get("method", "POST")).upper()
        path = str(request_data.get("path", "/"))
        headers = request_data.get("headers", {})
        body = request_data.get("body", None)
        timeout = request_data.get("timeout", 10)

        base_url = self.http_url_var.get().strip().rstrip("/")
        if not base_url:
            self._log("HTTP Base URL is empty.")
            return

        url = f"{base_url}{path if path.startswith('/') else '/' + path}"
        self._log(f"Sending HTTP request: {method} {url}")

        def do_request() -> None:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body,
                    timeout=timeout,
                )
                preview = response.text[:2000]
                self._log(
                    f"HTTP response: status={response.status_code}, "
                    f"reason={response.reason}, body={preview}"
                )
            except Exception as exc:
                self._log(f"HTTP request error: {exc}")

        threading.Thread(target=do_request, daemon=True).start()

    def _on_ws_open(self, _ws) -> None:
        self.ws_connected = True
        self._log("WebSocket connected.")

    def _on_ws_message(self, _ws, message: str) -> None:
        self._log(f"WebSocket received: {message}")

    def _on_ws_error(self, _ws, error) -> None:
        self._log(f"WebSocket error: {error}")

    def _on_ws_close(self, _ws, close_status_code, close_msg) -> None:
        self.ws_connected = False
        self._log(f"WebSocket closed. code={close_status_code}, message={close_msg}")


def main() -> None:
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
