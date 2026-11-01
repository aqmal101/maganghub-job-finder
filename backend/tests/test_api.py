import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.main import app


def make_client(tmp_path: Path) -> TestClient:
    (tmp_path / "master").mkdir()
    (tmp_path / "changes").mkdir()
    (tmp_path / "monitoring").mkdir()
    (tmp_path / "master" / "jobs.json").write_text(
        json.dumps([
            {
                "listing": {
                    "url": "https://example.test/jobs/1",
                    "title": "Python Intern",
                    "company": "Example",
                    "location": "Jakarta",
                },
                "detail": {"title": "Python Intern"},
                "scraping_status": "success",
            },
            {
                "listing": {
                    "url": "https://example.test/jobs/2",
                    "title": "Design Intern",
                    "company": "Studio",
                    "location": "Bandung",
                },
                "detail": {},
                "scraping_status": "partial",
            },
        ]),
        encoding="utf-8",
    )
    (tmp_path / "changes" / "changes.json").write_text("[]", encoding="utf-8")
    (tmp_path / "changes" / "pending.json").write_text("[]", encoding="utf-8")
    (tmp_path / "monitoring" / "monitoring_report.json").write_text(
        json.dumps({
            "generated_at": "2026-11-01T10:00:00+07:00",
            "batch_at": "2026-11-01T09:00:00+07:00",
            "summary": {"new_jobs": 1},
        }),
        encoding="utf-8",
    )
    return TestClient(app)


def test_jobs_pagination_and_filter(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    client = make_client(tmp_path)

    response = client.get("/api/v1/jobs", params={"search": "python"})

    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1


def test_job_detail_and_health(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    client = make_client(tmp_path)

    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").json() == {"status": "ready"}
    assert client.get(
        "/api/v1/jobs/https://example.test/jobs/1"
    ).status_code == 200


def test_public_api_has_no_write_route(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    client = make_client(tmp_path)

    assert client.post("/api/v1/jobs").status_code == 405


def test_rate_limit_returns_429(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "rate_limit_jobs", 1)
    client = TestClient(app, client=("127.0.0.2", 50000))

    assert client.get("/api/v1/jobs").status_code == 200
    assert client.get("/api/v1/jobs").status_code == 429
