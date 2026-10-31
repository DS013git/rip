"""Focused checks for status classification and offline sample loading."""

from ripgit.fetch import classify_status, load_sample_data


def test_status_thresholds() -> None:
    assert classify_status(0) == "alive"
    assert classify_status(30) == "alive"
    assert classify_status(31) == "dying"
    assert classify_status(90) == "dying"
    assert classify_status(91) == "dead"


def test_sample_data_loads_offline_and_has_all_statuses(monkeypatch) -> None:
    import requests

    def unexpected_request(*args, **kwargs):
        raise AssertionError("sample data must not make network requests")

    monkeypatch.setattr(requests, "get", unexpected_request)
    repos = load_sample_data()

    assert len(repos) == 12
    assert {repo["status"] for repo in repos} == {"alive", "dying", "dead"}
    assert repos[0]["name"] == "todo-app-v7-final"
    assert len(load_sample_data(limit=3)) == 3
