import os
from typing import Any

import httpx

from app.services.scanner.base import (
    AuditRecord,
    ScannerAdapter,
    ScannerError,
    ScoreRecord,
)

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
PSI_CATEGORIES = ("performance", "seo", "accessibility", "best-practices")


def _category_score(categories: dict[str, Any], key: str) -> float | None:
    raw = categories.get(key, {}).get("score")
    return None if raw is None else float(raw) * 100


def _audit_numeric(audits: dict[str, Any], key: str) -> float | None:
    raw = audits.get(key, {}).get("numericValue")
    return None if raw is None else float(raw)


class LighthouseAdapter(ScannerAdapter):
    def __init__(self, api_key: str | None = None, timeout: float = 180.0) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get(
            "PAGESPEED_API_KEY", ""
        )
        self.timeout = timeout

    def fetch_scores(self, url: str) -> ScoreRecord:
        params: list[tuple[str, str]] = [
            ("url", url),
            ("strategy", "mobile"),
        ]
        for cat in PSI_CATEGORIES:
            params.append(("category", cat))
        if self.api_key:
            params.append(("key", self.api_key))

        try:
            response = httpx.get(PSI_ENDPOINT, params=params, timeout=self.timeout)
        except httpx.HTTPError as exc:
            raise ScannerError(f"PSI request failed: {exc}") from exc

        if response.status_code != 200:
            raise ScannerError(
                f"PSI returned HTTP {response.status_code}: {response.text[:200]}"
            )

        body = response.json()
        lh = body.get("lighthouseResult", {})
        categories = lh.get("categories", {})
        audits = lh.get("audits", {})

        return ScoreRecord(
            performance_score=_category_score(categories, "performance"),
            seo_score=_category_score(categories, "seo"),
            accessibility_score=_category_score(categories, "accessibility"),
            best_practices_score=_category_score(categories, "best-practices"),
            lcp_ms=_audit_numeric(audits, "largest-contentful-paint"),
            inp_ms=_audit_numeric(audits, "interaction-to-next-paint"),
            cls=_audit_numeric(audits, "cumulative-layout-shift"),
            audits=_extract_audit_records(categories, audits),
        )


def _extract_audit_records(
    categories: dict[str, Any], audits: dict[str, Any]
) -> list[AuditRecord]:
    records: list[AuditRecord] = []
    for category_name, category_data in categories.items():
        for ref in category_data.get("auditRefs", []) or []:
            audit_id = ref.get("id")
            if not audit_id:
                continue
            audit = audits.get(audit_id, {})
            records.append(
                AuditRecord(
                    audit_id=audit_id,
                    title=audit.get("title", ""),
                    category=category_name,
                    score=audit.get("score"),
                    display_value=audit.get("displayValue"),
                )
            )
    return records
