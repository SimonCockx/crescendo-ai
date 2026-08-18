"""
Minimal client for the systemd sd_notify protocol.

Lets the service tell systemd it's ready, and periodically "pet" the
watchdog so systemd can detect a hung (not just crashed) process and
restart it. This has no effect - and no dependency requirements - when
not running under systemd (NOTIFY_SOCKET unset), so it's safe to call
unconditionally, e.g. during local development.
"""

import os
import socket


def notify(state: str) -> None:
    """
    Send a state notification to systemd, if running under it.

    Args:
        state: sd_notify state string, e.g. 'READY=1' or 'WATCHDOG=1'
    """
    address = os.environ.get('NOTIFY_SOCKET')
    if not address:
        return

    if address.startswith('@'):
        address = '\0' + address[1:]

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.connect(address)
            sock.sendall(state.encode())
    except OSError:
        pass
