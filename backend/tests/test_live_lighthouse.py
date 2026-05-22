"""Live integration test: real PSI calls against docs/target_websites.md.

Opt-in via `RUN_LIVE_LIGHTHOUSE=1` so the default `pytest` run stays fast and
deterministic. Also requires PAGESPEED_API_KEY in the environment.

Baselines are derived from `data/SEO_Page Score.xlsx` and documented in
`docs/lighthouse_baselines.md`.
"""

import os
import re
from pathlib import Path

import pytest

from app.services import scan_runner
from app.services.scanner.lighthouse import LighthouseAdapter

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_LIST = REPO_ROOT / "docs" / "target_websites.md"

# Lower-bound bands per URL. Source: docs/lighthouse_baselines.md.
EXPECTED_BANDS: dict[str, dict[str, int]] = {
    "https://adventure.inc/": {
        "performance": 50, "accessibility": 80, "best_practices": 70, "seo": 70,
    },
    "https://adventure.inc/about-us": {
        "performance": 30, "accessibility": 70, "best_practices": 60, "seo": 60,
    },
    "https://adventure.inc/hotels": {
        "performance": 50, "accessibility": 80, "best_practices": 70, "seo": 70,
    },
    "https://adventure.inc/hotels/tokyo/tokyo-lp-house-1444228": {
        "performance": 40, "accessibility": 80, "best_practices": 70, "seo": 60,
    },
}

_DEFAULT_BAND = {
    "performance": 0, "accessibility": 0, "best_practices": 0, "seo": 0,
}


def _load_target_urls() -> list[str]:
    if not TARGET_LIST.exists():
        return []
    return re.findall(r"<(https?://[^>]+)>", TARGET_LIST.read_text())


pytestmark = pytest.mark.skipif(
    not (os.environ.get("RUN_LIVE_LIGHTHOUSE") and os.environ.get("PAGESPEED_API_KEY")),
    reason="Live PSI tests require RUN_LIVE_LIGHTHOUSE=1 and PAGESPEED_API_KEY",
)


@pytest.mark.parametrize("url", _load_target_urls())
def test_target_url_lighthouse_metrics(url: str) -> None:
    """Per URL — checks FR-03 (4 scores), FR-08 (audits), and baseline bands.

    Uses `scan_runner._fetch_with_retry` so we exercise the same 3-retry / 1-2-4 s
    backoff path production uses. This tolerates PSI's occasional transient HTTP 500
    ("Lighthouse returned error: Something went wrong"), which is a Google-side flake
    we observed and which the production runner already handles.
    """
    band = EXPECTED_BANDS.get(url, _DEFAULT_BAND)
    result, error_reason, _retry_count = scan_runner._fetch_with_retry(
        LighthouseAdapter(), url
    )
    assert result is not None, f"all retries failed for {url}: {error_reason}"

    # FR-03: all 4 category scores must be present.
    assert result.performance_score is not None, f"performance missing for {url}"
    assert result.seo_score is not None, f"seo missing for {url}"
    assert result.accessibility_score is not None, f"accessibility missing for {url}"
    assert result.best_practices_score is not None, f"best_practices missing for {url}"

    # FR-08: per-audit evidence must be present.
    assert len(result.audits) > 50, f"expected >50 audits, got {len(result.audits)} for {url}"
    for audit in result.audits:
        assert audit.audit_id, f"audit_id missing on a record for {url}"
        assert audit.category in {
            "performance", "seo", "accessibility", "best-practices",
        }, f"unexpected category {audit.category!r} for {url}"

    # Baseline lower-bounds from docs/lighthouse_baselines.md.
    assert result.performance_score >= band["performance"], (
        f"performance {result.performance_score} below band {band['performance']} for {url}"
    )
    assert result.accessibility_score >= band["accessibility"], (
        f"accessibility {result.accessibility_score} below band {band['accessibility']} for {url}"
    )
    assert result.best_practices_score >= band["best_practices"], (
        f"best_practices {result.best_practices_score} below band {band['best_practices']} for {url}"
    )
    assert result.seo_score >= band["seo"], (
        f"seo {result.seo_score} below band {band['seo']} for {url}"
    )
