"""
ENGINE - The brains that runs everything.
Takes a plugin + target + credentials and runs the attack with threading.
"""

import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
from plugins.base import PluginBase
from core.result import Result, ResultCollection
from utils.logger import Logger


class Engine:
    def __init__(self, plugin: PluginBase, threads: int = 10,
                 stop_on_success: bool = False, verbose: bool = False):
        self.plugin = plugin
        self.threads = threads
        self.stop_on_success = stop_on_success
        self.verbose = verbose
        self.logger = Logger(verbose=verbose)
        self.results = ResultCollection()
        self._stop = False

    def run(self, host: str, port: int,
            usernames: list[str], passwords: list[str]) -> ResultCollection:
        self.logger.info(f"Target: {host}:{port} ({self.plugin.name})")
        self.logger.info(
            f"Credentials: {len(usernames)} users x "
            f"{len(passwords)} passwords = "
            f"{len(usernames) * len(passwords)} combos"
        )
        self.logger.info(f"Threads: {self.threads}")
        self.logger.info("")

        if not self.plugin.validate_target(host, port):
            self.logger.warning(
                f"Target doesn't appear to be running {self.plugin.name}. "
                f"Continuing anyway..."
            )

        combos = list(itertools.product(usernames, passwords))
        self.logger.info("Starting attack...\n")

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_combo = {
                executor.submit(
                    self._try_credential, host, port, username, password
                ): (username, password)
                for username, password in combos
            }

            for future in as_completed(future_to_combo):
                if self._stop:
                    break
                result = future.result()
                if result:
                    self.results.add(result)
                    if result.success:
                        self.logger.success(
                            f"FOUND: {result.username}:{result.password} "
                            f"@ {host}:{port}"
                        )
                        if self.stop_on_success:
                            self._stop = True

        return self.results

    def _try_credential(self, host: str, port: int,
                        username: str, password: str) -> Result | None:
        if self._stop:
            return None
        self.logger.attempt(f"Trying {username}:{password}")
        success = self.plugin.attempt(host, port, username, password)
        return Result(
            host=host, port=port, protocol=self.plugin.name,
            username=username, password=password, success=success,
        )
