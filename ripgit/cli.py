"""Command-line entry point for RIP.git."""

import argparse

from ripgit.build_site import build_site
from ripgit.fetch import fetch_repositories, load_sample_data
from ripgit.narrator import generate_haunting, narrate_repositories


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
    args = parser.parse_args()
    if not args.sample and not args.username:
        parser.error("username is required unless --sample is used")

    repos = (
        load_sample_data(args.limit)
        if args.sample
        else fetch_repositories(args.username, limit=args.limit)
    )
    narrated = narrate_repositories(repos, model=args.model)
    haunting = generate_haunting(narrated, model=args.model)
    username = args.username or "Demo Developer"
    output = build_site(narrated, username, haunting)
    fallback_count = sum(repo["narration_fallback"] for repo in narrated)
    gemma_count = len(narrated) - fallback_count
    print(f"Repos processed: {len(narrated)}")
    print(f"Gemma used: {gemma_count} | fallback used: {fallback_count}")
    print(f"Output: {output}")


if __name__ == "__main__":
    main()
