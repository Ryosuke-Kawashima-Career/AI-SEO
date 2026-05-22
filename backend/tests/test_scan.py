from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import select

from app.models.lighthouse_audit import LighthouseAudit
from app.models.scan_job import ScanJob
from app.models.scan_result import ScanResult
from app.models.url import RegisteredUrl
from app.services import scan_runner
from app.services.scanner.base import AuditRecord, ScannerError, ScoreRecord


def _make_score_record(audit_ids: list[str] | None = None) -> ScoreRecord:
    audit_ids = audit_ids or ["image-alt"]
    audits = [
        AuditRecord(
            audit_id=aid,
            title=aid.replace("-", " ").title(),
            category="accessibility",
            score=0.0,
            display_value="4 elements",
        )
        for aid in audit_ids
    ]
    return ScoreRecord(
        performance_score=80.0,
        seo_score=70.0,
        accessibility_score=90.0,
        best_practices_score=85.0,
        lcp_ms=2500.0,
        inp_ms=200.0,
        cls=0.05,
        audits=audits,
    )


def test_post_scan_returns_202_with_job_id(client):
    client.post("/api/urls", json={"url": "https://adventure.inc/"})

    with patch("app.api.scan._execute_in_background") as mock_bg:
        response = client.post("/api/scan")

    assert response.status_code == 202
    body = response.json()
    assert "job_id" in body and body["job_id"] >= 1
    mock_bg.assert_called_once_with(body["job_id"])


def test_execute_marks_job_completed(test_db_session, monkeypatch):
    monkeypatch.setattr("app.services.scan_runner.time.sleep", lambda _x: None)
    test_db_session.add(RegisteredUrl(url="https://adventure.inc/"))
    test_db_session.commit()

    adapter = MagicMock()
    adapter.fetch_scores.return_value = _make_score_record()

    job_id = scan_runner.create_job("manual", test_db_session)
    scan_runner.execute(job_id, test_db_session, adapter=adapter)

    job = test_db_session.get(ScanJob, job_id)
    assert job is not None
    assert job.status == "completed"
    assert job.success_count == 1
    assert job.failure_count == 0


def test_execute_inserts_scan_result_per_registered_url(test_db_session, monkeypatch):
    monkeypatch.setattr("app.services.scan_runner.time.sleep", lambda _x: None)
    for url in (
        "https://adventure.inc/",
        "https://adventure.inc/about-us",
        "https://adventure.inc/hotels",
    ):
        test_db_session.add(RegisteredUrl(url=url))
    test_db_session.commit()

    adapter = MagicMock()
    adapter.fetch_scores.return_value = _make_score_record()

    job_id = scan_runner.create_job("manual", test_db_session)
    scan_runner.execute(job_id, test_db_session, adapter=adapter)

    results = list(
        test_db_session.execute(
            select(ScanResult).where(ScanResult.job_id == job_id)
        ).scalars().all()
    )
    assert len(results) == 3
    assert all(r.status == "success" for r in results)


def test_execute_persists_lighthouse_audits(test_db_session, monkeypatch):
    monkeypatch.setattr("app.services.scan_runner.time.sleep", lambda _x: None)
    test_db_session.add(RegisteredUrl(url="https://adventure.inc/"))
    test_db_session.commit()

    adapter = MagicMock()
    adapter.fetch_scores.return_value = _make_score_record(
        audit_ids=["image-alt", "meta-description", "offscreen-images"]
    )

    job_id = scan_runner.create_job("manual", test_db_session)
    scan_runner.execute(job_id, test_db_session, adapter=adapter)

    audits = list(test_db_session.execute(select(LighthouseAudit)).scalars().all())
    persisted_ids = {a.audit_id for a in audits}
    assert persisted_ids == {"image-alt", "meta-description", "offscreen-images"}


def test_execute_marks_failed_after_three_retries(test_db_session, monkeypatch):
    monkeypatch.setattr("app.services.scan_runner.time.sleep", lambda _x: None)
    # Deliberately use an unregistered subdomain so a real PSI call would fail;
    # the adapter is mocked here, so this string is only a label.
    test_db_session.add(RegisteredUrl(url="https://failing.adventure.inc/"))
    test_db_session.commit()

    adapter = MagicMock()
    adapter.fetch_scores.side_effect = ScannerError("rate limit exceeded")

    job_id = scan_runner.create_job("manual", test_db_session)
    scan_runner.execute(job_id, test_db_session, adapter=adapter)

    result = test_db_session.execute(select(ScanResult)).scalar_one()
    assert result.status == "failed"
    assert result.retry_count == 3
    assert adapter.fetch_scores.call_count == 4  # initial + 3 retries

    job = test_db_session.get(ScanJob, job_id)
    assert job is not None
    assert job.failure_count == 1
    assert job.success_count == 0
