"""
HTTP BASIC AUTH PLUGIN
Tests HTTP Basic Authentication by sending credentials in the Authorization header.
"""

import requests
from requests.auth import HTTPBasicAuth
from plugins.base import PluginBase


class HTTPBasicPlugin(PluginBase):
    name = "http-basic"
    default_port = 80

    def attempt(self, host: str, port: int, username: str, password: str) -> bool:
        url = f"http://{host}:{port}/"
        try:
            response = requests.get(
                url,
                auth=HTTPBasicAuth(username, password),
                timeout=5,
                allow_redirects=True,
                verify=False,
            )
            if response.status_code in range(200, 300):
                return True
            return False
        except requests.exceptions.RequestException:
            return False

    def validate_target(self, host: str, port: int) -> bool:
        url = f"http://{host}:{port}/"
        try:
            response = requests.get(url, timeout=5, verify=False)
            if response.status_code == 401:
                auth_header = response.headers.get("WWW-Authenticate", "")
                if "Basic" in auth_header:
                    return True
            return False
        except requests.exceptions.RequestException:
            return False
