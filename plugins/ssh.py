"""
SSH PLUGIN - Test SSH credentials (passwords + key-based auth)

HOW SSH AUTH WORKS:
1. Client connects to server on port 22
2. They exchange encryption keys
3. Client tries to authenticate with username + password
4. Server responds: success or failure
"""

import paramiko
import socket
from plugins.base import PluginBase


class SSHPlugin(PluginBase):
    name = "ssh"
    default_port = 22

    def attempt(self, host: str, port: int, username: str, password: str) -> bool:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=5,
                allow_agent=False,
                look_for_keys=False,
                banner_timeout=5,
            )
            return True

        except paramiko.AuthenticationException:
            return False

        except (paramiko.SSHException, socket.error, socket.timeout,
                ConnectionRefusedError, OSError):
            return False

        finally:
            client.close()

    def validate_target(self, host: str, port: int) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            banner = sock.recv(1024).decode(errors="ignore")
            sock.close()
            return banner.startswith("SSH-")
        except (socket.error, OSError):
            return False
