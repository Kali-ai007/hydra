#!/usr/bin/env python3
"""
HYDRA - Expandable Credential Testing Tool

Usage:
    python hydra.py -t 192.168.1.100 -p http-basic -u admin -w wordlists/common.txt
    python hydra.py --list-plugins
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from plugins import get_plugin, list_plugins, discover_plugins
from core.engine import Engine
from utils.logger import Logger


def load_file_lines(filepath: str) -> list[str]:
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f if line.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hydra - Expandable Credential Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -t 192.168.1.100 -p http-basic -u admin -w wordlists/common.txt
  %(prog)s -t 10.0.0.1 --port 8080 -p http-basic -U users.txt -w passwords.txt -v
  %(prog)s --list-plugins
        """,
    )

    parser.add_argument("-t", "--target", help="Target host (IP or hostname)")
    parser.add_argument("--port", type=int, help="Target port (default: plugin default)")
    parser.add_argument("-p", "--plugin", help="Protocol plugin to use (e.g., http-basic)")

    user_group = parser.add_mutually_exclusive_group()
    user_group.add_argument("-u", "--username", help="Single username to test")
    user_group.add_argument("-U", "--username-file", help="File with usernames (one per line)")

    pass_group = parser.add_mutually_exclusive_group()
    pass_group.add_argument("-w", "--wordlist", help="Password wordlist file")
    pass_group.add_argument("-P", "--password", help="Single password to test")

    parser.add_argument("-T", "--threads", type=int, default=10, help="Parallel threads (default: 10)")
    parser.add_argument("-s", "--stop-on-success", action="store_true", help="Stop after first success")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show every attempt")
    parser.add_argument("-o", "--output", help="Save results to JSON file")
    parser.add_argument("--list-plugins", action="store_true", help="List available plugins")

    return parser


def main():
    logger = Logger()
    logger.banner()

    parser = build_parser()
    args = parser.parse_args()

    discover_plugins()

    if args.list_plugins:
        plugins = list_plugins()
        logger.info("Available plugins:\n")
        for name, plugin_cls in plugins.items():
            print(f"  {name:20s} (default port: {plugin_cls.default_port})")
        print()
        return

    if not args.target:
        parser.error("Target (-t) is required")
    if not args.plugin:
        parser.error("Plugin (-p) is required")

    try:
        plugin = get_plugin(args.plugin)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    port = args.port or plugin.default_port

    if args.username:
        usernames = [args.username]
    elif args.username_file:
        usernames = load_file_lines(args.username_file)
    else:
        parser.error("Username (-u) or username file (-U) is required")

    if args.wordlist:
        passwords = load_file_lines(args.wordlist)
    elif args.password:
        passwords = [args.password]
    else:
        parser.error("Wordlist (-w) or password (-P) is required")

    engine = Engine(
        plugin=plugin, threads=args.threads,
        stop_on_success=args.stop_on_success, verbose=args.verbose,
    )

    results = engine.run(host=args.target, port=port,
                         usernames=usernames, passwords=passwords)

    print(results.summary())

    successes = results.get_successes()
    if successes:
        logger.info("\nValid credentials found:")
        for r in successes:
            logger.success(f"  {r.username}:{r.password}")

    if args.output:
        results.save_json(args.output)
        logger.info(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
