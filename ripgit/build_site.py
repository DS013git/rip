"""Render the repository facts and epitaphs as a self-contained static page."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def build_site(
    repos: list[dict[str, Any]],
    username: str,
    haunting: list[dict[str, Any]] | None = None,
    output_path: Path | None = None,
) -> Path:
    """Write and return ``docs/index.html`` (or an explicitly supplied path)."""
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml", "j2"]),
    )
    template = environment.get_template("graveyard.html.j2")
    oldest_days = max((repo.get("days_since_last_push", 0) for repo in repos), default=0)
    html = template.render(
        username=username,
        repos=repos,
        haunting=haunting or [],
        total_repos=len(repos),
        dead_count=sum(repo.get("status") == "dead" for repo in repos),
        dying_count=sum(repo.get("status") == "dying" for repo in repos),
        oldest_days=oldest_days,
    )
    destination = output_path or PROJECT_ROOT / "docs" / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8")
    return destination
