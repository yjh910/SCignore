"""
main.py (scr_ignore.py) — Entry point for SC:R Ignore Tool.

Run this file to launch the application:
    python scr_ignore.py

Project layout
--------------
scr_ignore.py     ← entry point (this file)
config.py         ← constants (proxy host/port, URL pattern)
proxy_settings.py ← Windows system proxy management (winreg)
proxy_server.py   ← HTTP proxy server and player ID detection
gui.py            ← tkinter UI

Requirements: pip install pyperclip
"""

import tkinter as tk
from gui import App

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("460x480")
    App(root)
    root.mainloop()
