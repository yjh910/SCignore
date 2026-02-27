"""
proxy_settings.py — Windows system proxy management.

Sets / clears the IE/WinINet proxy via the registry and immediately
broadcasts the change so running apps (including SC:R) pick it up.

Key fix: Windows keeps "<local>" in ProxyOverride by default, which
makes 127.0.0.1 bypass the proxy entirely. We clear that bypass when
enabling so SC:R's localhost API calls actually reach our proxy.
"""

import winreg
import ctypes

from config import PROXY_HOST, PROXY_PORT

_REG_PATH     = r"Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
_saved_override: str = "<local>"   # restored when proxy is disabled


def _refresh_wininet() -> None:
    """Notify WinINet apps that proxy settings have changed."""
    wininet = ctypes.windll.wininet
    wininet.InternetSetOptionW(0, 39, 0, 0)  # INTERNET_OPTION_SETTINGS_CHANGED
    wininet.InternetSetOptionW(0, 37, 0, 0)  # INTERNET_OPTION_REFRESH


def set_system_proxy(enable: bool) -> None:
    """Enable or disable the system HTTP proxy pointing at our local server."""
    global _saved_override

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _REG_PATH,
        0, winreg.KEY_READ | winreg.KEY_WRITE,
    )

    if enable:
        # Save the current bypass list so we can restore it later
        try:
            _saved_override, _ = winreg.QueryValueEx(key, "ProxyOverride")
        except OSError:
            _saved_override = "<local>"

        winreg.SetValueEx(key, "ProxyEnable",   0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "ProxyServer",   0, winreg.REG_SZ,
                          f"{PROXY_HOST}:{PROXY_PORT}")
        # Clear the bypass list — this is the critical step.
        # The default "<local>" entry causes Windows to skip the proxy for
        # all 127.x.x.x addresses, which is exactly where SC:R's API lives.
        winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "")
    else:
        winreg.SetValueEx(key, "ProxyEnable",   0, winreg.REG_DWORD, 0)
        # Restore the bypass list to what it was before we started
        winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, _saved_override)

    winreg.CloseKey(key)
    _refresh_wininet()
