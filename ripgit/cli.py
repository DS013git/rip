"""Command-line entry point for RIP.git."""

import argparse


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ripgit.cli", description="Build a spooky graveyard for GitHub repositories.")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="Build a graveyard site")
    build.add_argument("username", nargs="?", help="GitHub username (optional with --sample)")
    build.add_argument("--sample", action="store_true", help="Use bundled offline demo data")
    build.add_argument("--limit", type=int, default=30, help="Maximum repositories to include (default: 30)")
    build.add_argument("--model", help="Override the Ollama model")
    return parser


def main() -> None:
    parser = make_parser()
    parser.parse_args()


if __name__ == "__main__":
    main()
