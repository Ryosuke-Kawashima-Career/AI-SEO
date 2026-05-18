from unittest.mock import MagicMock, patch

import pytest

from app.services.scanner.base import ScannerError
from app.services.scanner.lighthouse import LighthouseAdapter


def _psi_response(
    perf: float | None = 0.92,
    seo: float | None = 0.88,
    a11y: float | None = 0.74,
    bp: float | None = 0.95,
    lcp: float | None = 2800.0,
    inp: float | None = 180.0,
    cls: float | None = 0.08,
    extra_failing_audits: dict[str, dict] | None = None,
) -> dict:
    audits: dict[str, dict] = {
        "largest-contentful-paint": {
            "title": "LCP",
            "score": 0.5,
            "numericValue": lcp,
            "displayValue": "2.8 s",
        },
        "interaction-to-next-paint": {
            "title": "INP",
            "score": 0.7,
            "numericValue": inp,
            "displayValue": "180 ms",
        },
        "cumulative-layout-shift": {
            "title": "CLS",
            "score": 0.9,
            "numericValue": cls,
            "displayValue": "0.08",
        },
    }
    if extra_failing_audits:
        audits.update(extra_failing_audits)

    audit_refs_perf = [
        {"id": "largest-contentful-paint"},
        {"id": "interaction-to-next-paint"},
        {"id": "cumulative-layout-shift"},
    ]
    audit_refs_extra = [{"id": k} for k in (extra_failing_audits or {}).keys()]

    return {
        "lighthouseResult": {
            "categories": {
                "performance": {
                    "score": perf,
                    "auditRefs": audit_refs_perf + audit_refs_extra,
                },
                "seo": {"score": seo, "auditRefs": []},
                "accessibility": {"score": a11y, "auditRefs": []},
                "best-practices": {"score": bp, "auditRefs": []},
            },
            "audits": audits,
        }
    }


def _mock_get(status_code: int = 200, json_body: dict | None = None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_body or {}
    response.text = "" if status_code == 200 else "rate limit exceeded"
    return response


def test_valid_psi_response_populates_all_seven_fields():
    with patch("app.services.scanner.lighthouse.httpx.get") as mock_get:
        mock_get.return_value = _mock_get(200, _psi_response())
        result = LighthouseAdapter(api_key="dummy").fetch_scores("https://example.com")

    assert result.performance_score == 92.0
    assert result.seo_score == 88.0
    assert result.accessibility_score == 74.0
    assert result.best_practices_score == 95.0
    assert result.lcp_ms == 2800.0
    assert result.inp_ms == 180.0
    assert result.cls == 0.08


def test_missing_inp_field_yields_null():
    body = _psi_response(inp=None)
    body["lighthouseResult"]["audits"]["interaction-to-next-paint"].pop("numericValue")

    with patch("app.services.scanner.lighthouse.httpx.get") as mock_get:
        mock_get.return_value = _mock_get(200, body)
        result = LighthouseAdapter(api_key="dummy").fetch_scores("https://example.com")

    assert result.inp_ms is None
    assert result.lcp_ms == 2800.0
    assert result.cls == 0.08


def test_http_429_raises_scanner_error():
    with patch("app.services.scanner.lighthouse.httpx.get") as mock_get:
        mock_get.return_value = _mock_get(429, {})
        with pytest.raises(ScannerError) as exc_info:
            LighthouseAdapter(api_key="dummy").fetch_scores("https://example.com")
    assert "429" in str(exc_info.value)


def test_failing_audits_emitted_as_audit_records():
    failing = {
        "image-alt": {
            "title": "Image elements have `[alt]` attributes",
            "score": 0.0,
            "displayValue": "4 elements",
        },
        "offscreen-images": {
            "title": "Defer offscreen images",
            "score": 0.3,
            "displayValue": "Potential savings of 120 KiB",
        },
    }
    body = _psi_response(extra_failing_audits=failing)

    with patch("app.services.scanner.lighthouse.httpx.get") as mock_get:
        mock_get.return_value = _mock_get(200, body)
        result = LighthouseAdapter(api_key="dummy").fetch_scores("https://example.com")

    audit_ids = {a.audit_id for a in result.audits}
    assert "image-alt" in audit_ids
    assert "offscreen-images" in audit_ids
    # category attribution
    image_alt = next(a for a in result.audits if a.audit_id == "image-alt")
    assert image_alt.category == "performance"
    assert image_alt.score == 0.0
