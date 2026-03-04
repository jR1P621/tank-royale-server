import argparse
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_SERVICES = [
    "sample-bots",
    "example-bot",
    "chat-bot",
    "breakout-bot",
    "path-bot",
]


def parse_services(raw_services: str | None) -> list[str]:
    if not raw_services:
        return list(DEFAULT_SERVICES)
    return [service.strip() for service in raw_services.split(",") if service.strip()]


def run_compose(compose_args: list[str], repo_root: Path) -> int:
    container_runtime = os.getenv("CONTAINER_RUNTIME", "docker")
    command = [container_runtime, "compose"] + compose_args

    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=repo_root)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convenience utility to manage persistent non-neural bot services."
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="start",
        choices=["start", "stop", "status"],
        help="Action to run (default: start)",
    )
    parser.add_argument(
        "--services",
        default=None,
        help=(
            "Comma-separated service names to manage "
            f"(default: {','.join(DEFAULT_SERVICES)})"
        ),
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Skip image build during start action.",
    )
    parser.add_argument(
        "--with-deps",
        action="store_true",
        help="Start dependencies too (tank-royale-server and battle-controller).",
    )

    args = parser.parse_args()
    services = parse_services(args.services)

    if not services:
        print("No services specified.")
        return 1

    repo_root = Path(__file__).resolve().parents[1]

    print(f"Repository root: {repo_root}")
    print(f"Target non-neural services: {', '.join(services)}")

    if args.action == "start":
        compose_args = ["up", "-d"]
        if not args.with_deps:
            compose_args.append("--no-deps")
        if not args.no_build:
            compose_args.append("--build")
        compose_args.extend(services)
        return run_compose(compose_args, repo_root)

    if args.action == "stop":
        compose_args = ["stop"] + services
        return run_compose(compose_args, repo_root)

    compose_args = ["ps"] + services
    return run_compose(compose_args, repo_root)


if __name__ == "__main__":
    sys.exit(main())
