"""
RESULT - Clean structured container for credential test results.
"""

import json
from datetime import datetime


class Result:
    def __init__(self, host: str, port: int, protocol: str,
                 username: str, password: str, success: bool):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.username = username
        self.password = password
        self.success = success
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "host": self.host, "port": self.port, "protocol": self.protocol,
            "username": self.username, "password": self.password,
            "success": self.success, "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"[{status}] {self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"


class ResultCollection:
    def __init__(self):
        self.results: list[Result] = []

    def add(self, result: Result):
        self.results.append(result)

    def get_successes(self) -> list[Result]:
        return [r for r in self.results if r.success]

    def get_failures(self) -> list[Result]:
        return [r for r in self.results if not r.success]

    def to_json(self, successes_only: bool = True) -> str:
        if successes_only:
            data = [r.to_dict() for r in self.get_successes()]
        else:
            data = [r.to_dict() for r in self.results]
        return json.dumps(data, indent=2)

    def save_json(self, filepath: str, successes_only: bool = True):
        with open(filepath, "w") as f:
            f.write(self.to_json(successes_only))

    def summary(self) -> str:
        total = len(self.results)
        success = len(self.get_successes())
        return (
            f"\n{'='*50}\n"
            f"  SCAN COMPLETE\n"
            f"  Total attempts: {total}\n"
            f"  Successful:     {success}\n"
            f"  Failed:         {total - success}\n"
            f"{'='*50}"
        )
