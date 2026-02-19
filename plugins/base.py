"""
BASE PLUGIN - The blueprint for all protocol plugins.
Every plugin (HTTP, SSH, FTP, etc.) MUST follow this blueprint.
"""

from abc import ABC, abstractmethod


class PluginBase(ABC):
    name = ""
    default_port = 0

    @abstractmethod
    def attempt(self, host: str, port: int, username: str, password: str) -> bool:
        """Try ONE username/password combo against a target. Return True if it worked."""
        pass

    def validate_target(self, host: str, port: int) -> bool:
        """Optional: Check if the target is actually running this service."""
        return True

    def __repr__(self):
        return f"<Plugin: {self.name} (port {self.default_port})>"
