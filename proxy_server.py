"""
proxy_server.py — Loopback packet capture using WinDivert (pydivert).

Inspects TCP payloads on the loopback interface for SC:R's matchmaking
API pattern. Runs in SNIFF mode — packets are never blocked or delayed.

Requirements:
    pip install pydivert
    Run the application as Administrator (WinDivert driver requirement)
"""

import ctypes
import threading
from typing import Callable
from urllib.parse import unquote

try:
    import pydivert
    PYDIVERT_AVAILABLE = True
except ImportError:
    PYDIVERT_AVAILABLE = False

from config import SCR_PATTERN

# ── Internal state ────────────────────────────────────────────────────────────
_last_captured: str  = ""   # dedup for scr_mmgameloading
_last_selected: str  = ""   # dedup for scr_tooninfo
_on_found:    Callable[[str], None] | None = None   # loading screen opponent
_on_selected: Callable[[str], None] | None = None   # in-game profile click
_capture: "_Capture | None" = None


# ── Admin check ───────────────────────────────────────────────────────────────
def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


# ── Packet capture ────────────────────────────────────────────────────────────
class _Capture:
    """
    WinDivert-based loopback sniffer.

    Tries filters in order of preference.
    SNIFF mode (flags=1): packets are not intercepted — they flow through
    normally and we receive a read-only copy. No reinject needed.
    """

    # outbound is intentionally omitted: for loopback traffic, direction is
    # undefined at the NETWORK layer and combining them causes Error 87.
    _FILTERS = [
        "loopback and tcp.PayloadLength > 0",   # preferred (WinDivert 2.x)
        "tcp.PayloadLength > 0",                 # fallback (all TCP with payload)
    ]
    _SNIFF = 1   # WINDIVERT_FLAG_SNIFF — read-only, never blocks packets

    def __init__(self) -> None:
        self._handle: "pydivert.WinDivert | None" = None

    def start(self) -> None:
        last_err = None
        for f in self._FILTERS:
            try:
                self._handle = pydivert.WinDivert(f, flags=self._SNIFF)
                self._handle.open()
                threading.Thread(target=self._loop, daemon=True).start()
                return
            except OSError as e:
                last_err = e
                self._handle = None
                continue

        raise RuntimeError(
            f"WinDivert failed to open: {last_err}\n\n"
            "Make sure you are running this program as Administrator."
        )

    def stop(self) -> None:
        if self._handle:
            try:
                self._handle.close()
            except Exception:
                pass
            self._handle = None

    def _loop(self) -> None:
        try:
            for packet in self._handle:
                try:
                    self._inspect(bytes(packet.payload))
                except Exception:
                    pass
                # SNIFF mode — no reinject required
        except Exception:
            pass

    @staticmethod
    def _inspect(payload: bytes) -> None:
        """Check payload for the SC:R aurora-profile-by-toon URL pattern."""
        if b"aurora-profile-by-toon" not in payload:
            return

        try:
            first_line = payload.split(b"\r\n")[0].decode("utf-8", errors="replace")
        except Exception:
            return

        parts = first_line.split(" ", 2)
        if len(parts) < 2:
            return
        url = parts[1]

        if b"scr_mmgameloading" in payload:
            m = SCR_PATTERN.search(url)
            if m:
                _notify_found(unquote(m.group(1)))

        elif b"scr_tooninfo" in payload:
            m = SCR_PATTERN.search(url)
            if m:
                _notify_selected(unquote(m.group(1)))


# ── Player detection ──────────────────────────────────────────────────────────
def _notify_found(player_id: str) -> None:
    """Called on scr_mmgameloading — loading screen opponent."""
    global _last_captured
    if _last_selected and player_id.lower() == _last_selected.lower():
        return
    
    if player_id == _last_captured:
        return
    
    _last_captured = player_id
    
    if _on_found:
        _on_found(player_id)


def _notify_selected(player_id: str) -> None:
    """Called on scr_tooninfo — user clicked a player's profile in-game."""
    global _last_selected
    if player_id == _last_selected:
        return
    
    _last_selected = player_id
    if _on_selected:
        _on_selected(player_id)


# ── Public API ────────────────────────────────────────────────────────────────
def start_proxy(
    on_found:    Callable[[str], None],
    on_selected: Callable[[str], None] | None = None,
) -> None:
    """
    Start loopback packet capture.
    - on_found(player_id)    — scr_mmgameloading: loading screen opponent
    - on_selected(player_id) — scr_tooninfo: player profile clicked in-game
    Raises RuntimeError if pydivert is missing or not running as Administrator.
    """
    global _capture, _last_captured, _last_selected
    global _on_found, _on_selected

    if not PYDIVERT_AVAILABLE:
        raise RuntimeError(
            "pydivert is not installed.\n"
            "Run:  pip install pydivert\n"
            "Then restart as Administrator."
        )

    if not is_admin():
        raise RuntimeError(
            "This program must be run as Administrator.\n"
            "Right-click scr_ignore.py → Run as administrator."
        )

    _last_captured = ""
    _last_selected = ""
    _on_found      = on_found
    _on_selected   = on_selected

    _capture = _Capture()
    _capture.start()


def stop_proxy() -> None:
    """Stop packet capture."""
    global _capture
    if _capture:
        _capture.stop()
        _capture = None
