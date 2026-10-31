"""Checks for rendered self-contained graveyard pages."""

from ripgit.build_site import build_site


def test_render_contains_each_repo_and_both_epitaph_tones(tmp_path) -> None:
    repos = [
        {
            "name": "todo-app-v7-final",
            "description": "A todo list",
            "language": "Python",
            "stars": 2,
            "open_issues": 4,
            "days_since_last_push": 412,
            "status": "dead",
            "last_commit_message": "final cleanup",
            "cause_of_death": "Long silence after the last push",
            "gentle": "A quiet little app rests beneath the moon.",
            "savage": "Its final cleanup is taking a very long break.",
        },
        {
            "name": "portfolio-new-new",
            "description": "A portfolio refresh",
            "language": "HTML",
            "stars": 1,
            "open_issues": 1,
            "days_since_last_push": 45,
            "status": "dying",
            "last_commit_message": "adjust hero spacing",
            "cause_of_death": "A long pause in updates",
            "gentle": "A small light waits for another push.",
            "savage": "The hero spacing has had 45 days to reflect.",
        },
    ]
    output = tmp_path / "index.html"
    result = build_site(repos, "sample-user", [{"name": "portfolio-new-new", "whisper": "Commit soon!"}], output)
    html = result.read_text(encoding="utf-8")

    assert result == output
    assert "todo-app-v7-final" in html
    assert "portfolio-new-new" in html
    assert "A quiet little app rests beneath the moon." in html
    assert "Its final cleanup is taking a very long break." in html
    assert "The Haunting" in html and "Commit soon!" in html
    assert "data-status=\"dead\"" in html
    assert "Tone: Gentle Ghost" in html and "Tone: Savage Reaper" in html
    assert "https://" not in html.replace("https://github.com/your-username/rip-git", "")


def test_render_escapes_repo_content(tmp_path) -> None:
    repo = {
        "name": "<script>alert('x')</script>",
        "language": "Python",
        "stars": 0,
        "open_issues": 0,
        "days_since_last_push": 5,
        "status": "alive",
        "last_commit_message": "safe",
        "cause_of_death": "Still alive",
        "gentle": "Safe text.",
        "savage": "Also safe.",
    }
    html = build_site([repo], "demo", output_path=tmp_path / "index.html").read_text(encoding="utf-8")

    assert "&lt;script&gt;" in html
    assert "<script>alert('x')</script>" not in html


def test_phase_four_metadata_favicon_copy_and_empty_state(tmp_path) -> None:
    repo = {
        "name": "quiet-repo",
        "language": "Python",
        "stars": 0,
        "open_issues": 0,
        "days_since_last_push": 12,
        "status": "alive",
        "last_commit_message": "small update",
        "cause_of_death": "Still writing",
        "gentle": "A small light is still glowing.",
        "savage": "The repo has remembered how to commit.",
    }
    html = build_site([repo], "demo", output_path=tmp_path / "index.html").read_text(encoding="utf-8")

    assert "Your graveyard is empty. Suspiciously clean." in html
    assert "RIP quiet-repo, 12 days. Cause: Still writing." in html
    assert html.count("Copy my tombstone") == 1
    assert 'name="description"' in html
    assert "data:image/svg+xml" in html
    assert "navigator.clipboard.writeText" in html
