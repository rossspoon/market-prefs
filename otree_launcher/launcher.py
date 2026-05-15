#!/usr/bin/env python3
"""
oTree Session Creator — Launcher
Double-click this file (or run: python launcher.py) to start the app.
Opens automatically in your default browser.
"""

import sys
import os
import time
import socket
import threading
import webbrowser
import subprocess

PORT = 5055
URL = f"http://localhost:{PORT}"


def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) != 0


def wait_for_server(port, timeout=10):
    """Poll until Flask is accepting connections."""
    start = time.time()
    while time.time() - start < timeout:
        if not is_port_free(port):
            return True
        time.sleep(0.15)
    return False


def open_browser():
    if wait_for_server(PORT):
        webbrowser.open(URL)
    else:
        print(f"Server did not start in time. Open {URL} manually.")


def main():
    # Change to the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    if not is_port_free(PORT):
        print(f"Port {PORT} already in use — opening existing instance.")
        webbrowser.open(URL)
        return

    print("=" * 52)
    print("  oTree Session Creator")
    print(f"  Starting on {URL}")
    print("  Close this window to stop the app.")
    print("=" * 52)

    # Open browser slightly after Flask starts
    threading.Thread(target=open_browser, daemon=True).start()

    # Start Flask (blocks until Ctrl-C or window closed)
    try:
        from app import app
        app.run(port=PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nShutting down. Goodbye.")
    except ImportError as e:
        print(f"\nError: {e}")
        print("Make sure you've installed dependencies:")
        print("  pip install flask requests")
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
