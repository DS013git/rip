"""Mocked Ollama tests for parsing and deterministic fallback behavior."""

import json

import requests

from ripgit.narrator import generate_haunting, narrate_repositories


REPO = {
    "name": "todo-app-v7-final",
    "description": "A todo list",
    "language": "Python",
    "stars": 2,
    "open_issues": 4,
    "days_since_last_push": 412,
    "status": "dead",
    "last_commit_message": "final final cleanup",
}

GOOD_JSON = {
    "gentle": "The little app rests after 412 quiet days. Its last commit still glows.",
    "savage": "todo-app-v7-final has been quiet for 412 days. Even its final cleanup took a long break.",
    "cause_of_death": "Long silence after the last push",
}


class FakeResponse:
    def __init__(self, content: str):
        self.content = content

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"message": {"content": self.content}, "prompt_eval_count": 20, "eval_count": 12}


def test_valid_json_uses_one_ollama_call_and_traces_usage(monkeypatch, tmp_path) -> None:
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(json.dumps(GOOD_JSON))

    monkeypatch.setattr("ripgit.narrator.requests.post", post)
    trace = tmp_path / "trace.jsonl"
    result = narrate_repositories([REPO], trace_path=trace)[0]

    assert result["gentle"] == GOOD_JSON["gentle"]
    assert result["narration_fallback"] is False
    assert len(calls) == 1
    assert calls[0][0].endswith("/api/chat")
    assert calls[0][1]["json"]["stream"] is False
    assert calls[0][1]["json"]["format"] == "json"
    record = json.loads(trace.read_text(encoding="utf-8").strip())
    assert record["approx_tokens"] == 32
    assert record["valid_json"] is True


def test_fenced_json_is_parsed_without_retry(monkeypatch, tmp_path) -> None:
    calls = []

    def post(url, **kwargs):
        calls.append(url)
        return FakeResponse("```json\n" + json.dumps(GOOD_JSON) + "\n```")

    monkeypatch.setattr("ripgit.narrator.requests.post", post)
    result = narrate_repositories([REPO], trace_path=tmp_path / "trace.jsonl")[0]

    assert result["savage"] == GOOD_JSON["savage"]
    assert result["narration_fallback"] is False
    assert len(calls) == 1


def test_bad_json_retries_once_then_uses_fallback(monkeypatch, tmp_path, capsys) -> None:
    calls = []

    def post(url, **kwargs):
        calls.append(url)
        return FakeResponse("not json")

    monkeypatch.setattr("ripgit.narrator.requests.post", post)
    result = narrate_repositories([REPO], trace_path=tmp_path / "trace.jsonl")[0]

    assert result["narration_fallback"] is True
    assert result["cause_of_death"] == "Long silence after the last push"
    assert len(calls) == 2
    assert "todo-app-v7-final" in capsys.readouterr().out
    records = (tmp_path / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(records) == 2
    assert all(json.loads(line)["valid_json"] is False for line in records)


def test_connection_error_uses_fallback_without_retry(monkeypatch, tmp_path, capsys) -> None:
    calls = []

    def post(url, **kwargs):
        calls.append(url)
        raise requests.ConnectionError("Ollama is unavailable")

    monkeypatch.setattr("ripgit.narrator.requests.post", post)
    result = narrate_repositories([REPO], trace_path=tmp_path / "trace.jsonl")[0]

    assert result["narration_fallback"] is True
    assert "412 days" in result["gentle"]
    assert len(calls) == 1
    assert "Ollama fallback for todo-app-v7-final" in capsys.readouterr().out


def test_haunting_uses_one_call_for_at_most_three_dying_repos(monkeypatch, tmp_path) -> None:
    calls = []

    def post(url, **kwargs):
        calls.append(kwargs["json"])
        return FakeResponse(json.dumps({"whispers": ["Commit soon, little repo."] * 3}))

    repos = [
        {**REPO, "name": f"dying-{number}", "status": "dying"}
        for number in range(4)
    ]
    monkeypatch.setattr("ripgit.narrator.requests.post", post)
    haunting = generate_haunting(repos, trace_path=tmp_path / "trace.jsonl")

    assert len(calls) == 1
    assert len(calls[0]["messages"][1]["content"]) > 0
    facts = json.loads(calls[0]["messages"][1]["content"])
    assert [item["name"] for item in facts] == ["dying-0", "dying-1", "dying-2"]
    assert [item["name"] for item in haunting] == ["dying-0", "dying-1", "dying-2"]
    assert all(item["whisper"] == "Commit soon, little repo." for item in haunting)
