"""
gui.py — tkinter UI for SC:R Ignore Tool.

Start/stop lifecycle:
  - Start: begins WinDivert loopback capture via proxy_server
  - Stop / close: stops capture cleanly

Note: must be run as Administrator (WinDivert driver requirement).
"""

import atexit
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext, ttk

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

from proxy_server import is_admin, start_proxy, stop_proxy


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root        = root
        self.running     = False
        self._pending_id = ""   # most recent player ID — sent on F9
        root.title("SC:R Ignore")
        root.resizable(False, False)
        self._build_ui()
        root.protocol("WM_DELETE_WINDOW", self._on_close)
        atexit.register(self._cleanup)

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        # Admin warning banner
        if not is_admin():
            tk.Label(
                self.root,
                text="⚠  Not running as Administrator — capture will fail",
                bg="#cc0000", fg="white", font=("", 9, "bold"), pady=4,
            ).pack(fill=tk.X)

        # Status row
        sf = ttk.Frame(self.root, padding=(12, 6))
        sf.pack(fill=tk.X)
        self.dot    = tk.Label(sf, text="●", fg="#cc0000", font=("", 16))
        self.dot.pack(side=tk.LEFT)
        self.status = tk.StringVar(value="  Stopped")
        tk.Label(sf, textvariable=self.status).pack(side=tk.LEFT)

        # Start / Stop button
        self.btn = ttk.Button(self.root, text="▶  Start Monitoring",
                              command=self._toggle, width=26)
        self.btn.pack(padx=12, pady=4)

        # F9 hotkey hint
        if KEYBOARD_AVAILABLE:
            self.hotkey_var = tk.StringVar(value="F9  —  no player detected yet")
            ttk.Label(self.root, textvariable=self.hotkey_var,
                      foreground="#888888", font=("", 8)).pack(pady=(0, 2))
        else:
            ttk.Label(self.root,
                      text="Install 'keyboard' for F9 auto-type  (pip install keyboard)",
                      foreground="#cc6600", font=("", 8)).pack(pady=(0, 2))

        # In-game selected player (scr_tooninfo)
        sf2 = ttk.LabelFrame(self.root,
                             text=" Selected Player  (click profile in-game) ",
                             padding=8)
        sf2.pack(fill=tk.X, padx=12, pady=(2, 4))
        self.selected_var = tk.StringVar(value="—")
        tk.Label(sf2, textvariable=self.selected_var,
                 font=("Consolas", 12, "bold"), fg="#006633").pack()
        
        # Loading screen opponent (scr_mmgameloading)
        cf = ttk.LabelFrame(self.root,
                            text=" Match Opponent ",
                            padding=8)
        cf.pack(fill=tk.X, padx=12, pady=(4, 2))
        self.clip_var = tk.StringVar(value="—")
        tk.Label(cf, textvariable=self.clip_var,
                 font=("Consolas", 12, "bold"), fg="#003399").pack()
        ttk.Label(cf,
                  text="Will be updated when a match is made.",
                  foreground="gray").pack(anchor="w", pady=(2, 0))

        # History log
        lf = ttk.LabelFrame(self.root, text=" History ", padding=5)
        lf.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 12))
        self.log = scrolledtext.ScrolledText(
            lf, height=9, width=52, state=tk.DISABLED,
            font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4",
        )
        self.log.pack(fill=tk.BOTH, expand=True)

    # ── Controls ──────────────────────────────────────────────────────────────
    def _toggle(self) -> None:
        self._stop() if self.running else self._start()

    def _start(self) -> None:
        # Callbacks are called from capture thread → schedule on main thread
        on_found    = lambda pid:         self.root.after(0, self._on_player_found, pid)
        on_selected = lambda pid:         self.root.after(0, self._on_player_selected, pid)

        try:
            start_proxy(on_found, on_selected)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start:\n{e}")
            return

        if KEYBOARD_AVAILABLE:
            keyboard.add_hotkey('f9', self._send_ignore)
            keyboard.add_hotkey('f8', self._send_unignore)

        self.running = True
        self.dot.config(fg="#00aa00")
        self.status.set("  Active  (capturing loopback traffic)")
        self.btn.config(text="■  Stop")
        self._log("Started.")

    def _stop(self) -> None:
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.remove_hotkey('f9')
            except Exception:
                pass
        stop_proxy()
        self.running = False
        self.dot.config(fg="#cc0000")
        self.status.set("  Stopped")
        self.btn.config(text="▶  Start Monitoring")
        self._log("Stopped.")

    # ── Callbacks ─────────────────────────────────────────────────────────────
    def _on_player_found(self, player_id: str) -> None:
        """scr_mmgameloading — loading screen opponent detected."""
        self._pending_id = player_id
        self.clip_var.set(f"{player_id}")
        self._log(f"[match]    {player_id}")
        if KEYBOARD_AVAILABLE:
            self.hotkey_var.set(f"F9  →  /ignore {player_id}")

    def _on_player_selected(self, player_id: str) -> None:
        """scr_tooninfo — user clicked a player profile in-game."""
        self._pending_id = player_id
        self.selected_var.set(f"{player_id}")
        self._log(f"[selected] {player_id}")

    def _send_ignore(self) -> None:
        """F9 hotkey — type /ignore {player_id} into SC:R chat."""
        pid = self._pending_id
        if not pid:
            return
        threading.Thread(target=self._type_command,
                         args=(f"/ignore {pid}",), daemon=True).start()

    def _send_unignore(self) -> None:
        """F8 hotkey — type /unignore {player_id} into SC:R chat."""
        pid = self._pending_id
        if not pid:
            return
        threading.Thread(target=self._type_command, 
                         args=(f"/unignore {pid}",), daemon=True).start()

    def _type_command(self, cmd: str) -> None:
        """Type a chat command in-game: Enter → command → Enter."""
        keyboard.press_and_release('enter')
        time.sleep(0.2)
        keyboard.write(cmd, delay=0.05)
        time.sleep(0.05)
        keyboard.press_and_release('enter')
        self.root.after(0, self._log, f"Typed: {cmd}")

    def _log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, f"[{ts}] {msg}\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    # ── Cleanup ───────────────────────────────────────────────────────────────
    def _on_close(self) -> None:
        self._cleanup()
        self.root.destroy()

    def _cleanup(self) -> None:
        if self.running:
            stop_proxy()
