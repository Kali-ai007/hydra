#!/usr/bin/env python3
"""
HYDRA - Expandable Credential Testing Tool

USAGE:
    python hydra.py -t 192.168.1.100 -p http-basic -u admin -w passwords.txt
    echo '{"host":"192.168.1.1","port":22,"protocol":"ssh"}' | python hydra.py --pipe -u admin -w wordlists/common.txt
    python hydra.py --dashboard
    python hydra.py --list-plugins
"""

import argparse
import json
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


def parse_pipeline_input() -> list[dict]:
    targets = []
    if sys.stdin.isatty():
        print("Error: --pipe requires piped input. Example:")
        print('  echo \'{"host":"127.0.0.1","port":22,"protocol":"ssh"}\' | python hydra.py --pipe -u admin -w wordlists/common.txt')
        sys.exit(1)

    raw = sys.stdin.read().strip()
    if not raw:
        print("Error: No input received from pipe")
        sys.exit(1)

    try:
        data = json.loads(raw)
        if isinstance(data, list):
            targets = data
        elif isinstance(data, dict):
            targets = [data]
        else:
            print("Error: Invalid JSON format")
            sys.exit(1)
    except json.JSONDecodeError:
        for line_num, line in enumerate(raw.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                targets.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON on line {line_num}: {line}")
                sys.exit(1)

    for i, target in enumerate(targets):
        for field in ("host", "port", "protocol"):
            if field not in target:
                print(f"Error: Target {i+1} missing '{field}': {target}")
                sys.exit(1)

    return targets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hydra - Expandable Credential Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -t 192.168.1.100 -p http-basic -u admin -w wordlists/common.txt
  %(prog)s -t 10.0.0.1 --port 8080 -p http-basic -U users.txt -w passwords.txt -v
  echo '{"host":"10.0.0.1","port":22,"protocol":"ssh"}' | %(prog)s --pipe -u admin -w wordlists/common.txt
  %(prog)s --dashboard
  %(prog)s --list-plugins
        """,
    )

    parser.add_argument("-t", "--target", help="Target host (IP or hostname)")
    parser.add_argument("--port", type=int, help="Target port (default: plugin default)")
    parser.add_argument("-p", "--plugin", help="Protocol plugin to use")
    parser.add_argument("--pipe", action="store_true", help="Read targets from stdin as JSON")
    parser.add_argument("--dashboard", action="store_true", help="Start web dashboard")
    parser.add_argument("--dashboard-port", type=int, default=5000, help="Dashboard port (default: 5000)")

    user_group = parser.add_mutually_exclusive_group()
    user_group.add_argument("-u", "--username", help="Single username")
    user_group.add_argument("-U", "--username-file", help="Username file")

    pass_group = parser.add_mutually_exclusive_group()
    pass_group.add_argument("-w", "--wordlist", help="Password wordlist")
    pass_group.add_argument("-P", "--password", help="Single password")

    parser.add_argument("-T", "--threads", type=int, default=10, help="Threads (default: 10)")
    parser.add_argument("-s", "--stop-on-success", action="store_true", help="Stop after first success")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show every attempt")
    parser.add_argument("-o", "--output", help="Save results to JSON file")
    parser.add_argument("--list-plugins", action="store_true", help="List available plugins")

    return parser


def get_credentials(args):
    if args.username:
        usernames = [args.username]
    elif args.username_file:
        usernames = load_file_lines(args.username_file)
    else:
        print("Error: Username (-u) or username file (-U) is required")
        sys.exit(1)

    if args.wordlist:
        passwords = load_file_lines(args.wordlist)
    elif args.password:
        passwords = [args.password]
    else:
        print("Error: Wordlist (-w) or password (-P) is required")
        sys.exit(1)

    return usernames, passwords


def run_single_target(args, logger):
    if not args.target:
        print("Error: Target (-t) is required")
        sys.exit(1)
    if not args.plugin:
        print("Error: Plugin (-p) is required")
        sys.exit(1)

    try:
        plugin = get_plugin(args.plugin)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    port = args.port or plugin.default_port
    usernames, passwords = get_credentials(args)

    engine = Engine(
        plugin=plugin, threads=args.threads,
        stop_on_success=args.stop_on_success, verbose=args.verbose,
    )
    return engine.run(host=args.target, port=port,
                      usernames=usernames, passwords=passwords)


def run_pipeline_mode(args, logger):
    targets = parse_pipeline_input()
    usernames, passwords = get_credentials(args)

    logger.info(f"Pipeline mode: {len(targets)} targets received\n")

    all_results = []
    for i, target in enumerate(targets, 1):
        host = target["host"]
        port = int(target["port"])
        protocol = target["protocol"]

        logger.info(f"[{i}/{len(targets)}] Attacking {host}:{port} ({protocol})")

        try:
            plugin = get_plugin(protocol)
        except ValueError as e:
            logger.error(f"  Skipping: {e}")
            continue

        engine = Engine(
            plugin=plugin, threads=args.threads,
            stop_on_success=args.stop_on_success, verbose=args.verbose,
        )
        results = engine.run(host=host, port=port,
                             usernames=usernames, passwords=passwords)
        all_results.extend(results.results)

    from core.result import ResultCollection
    combined = ResultCollection()
    combined.results = all_results
    return combined


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

    if args.dashboard:
        from dashboard.app import start_dashboard
        start_dashboard(port=args.dashboard_port)
        return

    if args.pipe:
        results = run_pipeline_mode(args, logger)
    else:
        results = run_single_target(args, logger)

    print(results.summary())

    successes = results.get_successes()
    if successes:
        logger.info("\nValid credentials found:")
        for r in successes:
            logger.success(f"  {r.username}:{r.password} @ {r.host}:{r.port} ({r.protocol})")

    if args.output:
        results.save_json(args.output)
        logger.info(f"\nResults saved to: {args.output}")

    if args.pipe:
        for r in results.get_successes():
            print(json.dumps(r.to_dict()))


if __name__ == "__main__":
    main()
