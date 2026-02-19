"""
LOGGER - Pretty colored terminal output.
"""


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class Logger:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def success(self, message: str):
        print(f"{Colors.GREEN}{Colors.BOLD}[+]{Colors.RESET} {Colors.GREEN}{message}{Colors.RESET}")

    def error(self, message: str):
        print(f"{Colors.RED}[-]{Colors.RESET} {Colors.RED}{message}{Colors.RESET}")

    def warning(self, message: str):
        print(f"{Colors.YELLOW}[!]{Colors.RESET} {Colors.YELLOW}{message}{Colors.RESET}")

    def info(self, message: str):
        print(f"{Colors.BLUE}[*]{Colors.RESET} {message}")

    def attempt(self, message: str):
        if self.verbose:
            print(f"{Colors.GRAY}[.] {message}{Colors.RESET}")

    def banner(self):
        print(f"""{Colors.CYAN}{Colors.BOLD}
    ╦ ╦╦ ╦╔╦╗╦═╗╔═╗
    ╠═╣╚╦╝ ║║╠╦╝╠═╣
    ╩ ╩ ╩ ═╩╝╩╚═╩ ╩
    
    Credential Testing Tool v0.1.0
    Expandable Plugin Architecture
{Colors.RESET}""")
