"""
FTP PLUGIN - Test FTP credentials

WHAT IS FTP?
File Transfer Protocol - used to upload/download files to servers.
Still found on tons of internal networks, NAS devices, printers,
and legacy systems. Default creds are super common.

HOW FTP AUTH WORKS:
1. Connect to server on port 21
2. Send USER <username>
3. Send PASS <password>
4. Server responds: 230 (logged in) or 530 (access denied)

Python has ftplib built in - no extra install needed!
"""

import ftplib
import socket
from plugins.base import PluginBase


class FTPPlugin(PluginBase):
    name = "ftp"
    default_port = 21

    def attempt(self, host: str, port: int, username: str, password: str) -> bool:
        try:
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=5)
            ftp.login(username, password)
            ftp.quit()
            return True

        except ftplib.error_perm:
            # 530 Access denied - wrong credentials
            return False

        except (ftplib.all_errors, socket.error, socket.timeout,
                ConnectionRefusedError, OSError):
            return False

    def validate_target(self, host: str, port: int) -> bool:
        try:
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=5)
            banner = ftp.getwelcome()
            ftp.quit()
            # FTP banners start with status code like "220 Welcome"
            return banner.startswith("220")
        except (ftplib.all_errors, socket.error, OSError):
            return False
