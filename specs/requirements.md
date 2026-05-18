# Requirements Specification

> **Source**: [user_story.md](user_story.md)
> **Status**: Draft
> **Last Updated**: 2026-05-18

---

## Traceability Map

```text
User Story
  ├── FR-01  URL Management
  ├── FR-02  Automated SEO Score Retrieval
  ├── FR-03  SEO Score Dimensions
  ├── FR-04  Dashboard Display
  ├── FR-05  Historical Score Tracking
  ├── FR-06  Scheduled Automatic Scanning
  ├── FR-07  Score Change Comparison
  └── FR-08  SEO Improvement Suggestion
        ├── NFR-01 ~ NFR-08
        └── AC-01 ~ AC-11
```

---

## 1. Functional Requirements

### FR-01 — URL Management

| Item | Detail |
|---|---|
| **Description** | The system must allow an authorized user to register, update, and delete target page URLs for SEO monitoring. |
| **Input** | A valid, absolute URL (e.g., `https://example.com/flights`) |
| **Output** | The URL is persisted in the target page registry and becomes eligible for scanning. |
| **Constraints** | - URL must begin with `https://` or `http://`. |

---

### FR-02 — Automated SEO Score Retrieval

| Item | Detail |
|---|---|
| **Description** | The system must automatically retrieve SEO scores for all registered URLs without manual intervention. |
| **Input** | Registered URL list; trigger source (scheduled job or manual on-demand request) |
| **Output** | A structured score record per URL is persisted in the data store, timestamped to the second. |
| **Constraints** | - The system must use at least one external SEO scoring API. You should use **Lighthouse** so that the process of checking lighthouse on the browser can be **automated**. |

---

### FR-03 — SEO Score Dimensions

| Item | Detail |
|---|---|
| **Description** | Each scan result must capture a defined set of SEO metric dimensions to enable meaningful comparison over time. |
| **Dimensions (Required)** | 1. **Performance Score**: 0–100 composite score. 2. **SEO Score**: 0–100 technical SEO score of **Lighthouse** report. 3. **Accessibility Score**: 0–100. 4. **Best Practices Score**: 0–100. 5. **Core Web Vitals**: LCP (ms), INP (ms), CLS (unitless). |
| **Input** | Raw API response from the scoring engine |
| **Output** | Normalized score record conforming to the data schema defined in `design.md` |
| **Constraints** | - All five dimension groups are mandatory per scan record. - If an individual metric is unavailable, the value must be stored as `null`, not `0`. |

---

### FR-04 — Dashboard Display

| Item | Detail |
|---|---|
| **Description** | The system must present a visual dashboard displaying the latest SEO scores for all registered URLs. |
| **Input** | Latest scan records retrieved from the data store |
| **Output** | A rendered dashboard page showing, per URL: current scores for all dimensions in FR-03, scan timestamp, and a status indicator (pass / warning / fail) based on score thresholds. |
| **Constraints** | - Score threshold for "pass": ≥ 90. "Warning": 50–89. "Fail": < 50. - Dashboard must be accessible via a standard web browser without additional software installation.|

---

### FR-05 — Historical Score Tracking

| Item | Detail |
|---|---|
| **Description** | The system must store all scan results historically and allow the user to view score trends over time. |
| **Input** | User-selected URL and date range (date range picker) |
| **Output** | A time-series chart showing the score for each dimension across the selected period. |
| **Constraints** | - History must be retained for a minimum of 12 months. - The chart must support at least daily granularity. - The user must be able to export the historical data as CSV. |

---

### FR-06 — Scheduled Automatic Scanning

| Item | Detail |
|---|---|
| **Description** | The system must execute SEO scans on a configurable recurring schedule without manual intervention. |
| **Input** | Schedule configuration: frequency (`daily`, `weekly`) and time-of-day (HH:MM, UTC) |
| **Output** | A new scan job is enqueued and executed at the configured time; results are persisted per FR-02. |
| **Constraints** | - Default schedule is `daily` at `00:00 UTC`. - The system must send an execution result notification (success/failure count) to the configured administrator email within 15 minutes of job completion. |

---

### FR-07 — Score Change Comparison

| Item | Detail |
|---|---|
| **Description** | The system must allow the user to compare SEO scores between two specific scan dates to quantify the effect of SEO improvement measures. |
| **Input** | Target URL, Baseline date, Comparison date|
| **Output** | A comparison table showing, per dimension: baseline score, comparison score, and delta (Δ) with a positive (▲) or negative (▼) directional indicator. |
| **Constraints** | - Both selected dates must have existing scan records; otherwise the system must display an error message: "No scan record found for the selected date." - Delta is calculated as: `comparison_score - baseline_score`. |

---

### FR-08 — SEO Improvement Suggestion

| Item | Detail |
|---|---|
| **Description** | The system must generate actionable SEO improvement suggestions for a target URL, derived from (a) the latest Lighthouse audit findings and (b) the historical effect of previously applied measures recorded in the system, so that an SEO specialist can prioritize the most impactful improvements. |
| **Actor** | SEO Specialist |
| **Input** | Target URL; the latest scan record (FR-02 / FR-03); historical scan records (FR-05); the set of failing or sub-optimal Lighthouse audit items (`audits[].score < 0.9`). |
| **Output** | A ranked list of suggestions. Each suggestion item must contain: 1. **Affected Dimension** (e.g., Performance, SEO, Accessibility). 2. **Action Description** in plain language (e.g., "Add `alt` attributes to images"). 3. **Originating Lighthouse Audit ID** (e.g., `image-alt`). 4. **Estimated Score Impact** (Δ) per dimension, derived from past observed deltas (FR-07) of comparable measures. 5. **Confidence Level** (`high` / `medium` / `low`) based on historical sample size. |
| **Constraints** | - Suggestions must be ranked by descending **Estimated Score Impact** (Δ). - Each suggestion must cite the originating Lighthouse audit; suggestions without traceable evidence must not be displayed. - When no historical comparable measure exists, **Confidence Level** must default to `low` and Estimated Score Impact may be displayed as `N/A`. - The suggestion module must be encapsulated behind an adapter interface (per NFR-05) so the underlying inference engine can be replaced without altering dashboard logic. |

---

## 2. Non-Functional Requirements

| ID | Category | Requirement | Metric |
|---|---|---|---|
| **NFR-01** | Performance | Dashboard initial load time | < 3 seconds on a standard broadband connection (50 Mbps) |
| **NFR-02** | Availability | System uptime | ≥ 99.0% monthly, excluding scheduled maintenance windows |
| **NFR-03** | Scalability | Registered URL capacity | Must support ≥ 100 registered URLs with no degradation in scan throughput |
| **NFR-04** | Data Retention | Historical score storage | Scan records must be retained for a minimum of 12 months from the scan date |
| **NFR-05** | Maintainability | Scoring engine replaceability | The SEO scoring API integration must be encapsulated behind an adapter interface so that the provider can be swapped without modifying dashboard logic |
| **NFR-06** | Browser Compatibility | Supported browsers | Latest 2 major versions of Chrome, Firefox, Safari, and Edge |
| **NFR-07** | Performance (Suggestion) | Suggestion generation latency | < 5 seconds per URL on the latest scan record, measured server-side |
| **NFR-08** | Explainability | Suggestion traceability | Every suggestion must be traceable to (a) a specific Lighthouse audit ID and (b) the historical scan records used to estimate its impact; this mapping must be queryable via API for audit purposes |

---

## 3. Acceptance Criteria

### AC-01 — URL Registration (→ FR-01)

```gherkin
Given the user is logged in to the dashboard
When the user submits a valid URL "https://example-ota.com/flights"
Then the URL appears in the registered target page list
And a success message "URL registered successfully" is displayed
```

**Verification**: Manual UI test — register a new URL and confirm its presence in the list.

---

### AC-02 — Duplicate URL Rejection (→ FR-01)

```gherkin
Given "https://example-ota.com/flights" is already registered
When the user attempts to register the same URL again
Then the system rejects the request
And displays the error message "This URL is already registered"
```

**Verification**: Manual UI test — attempt to register a duplicate and confirm error handling.

---

### AC-03 — On-Demand Scan Execution (→ FR-02)

```gherkin
Given at least one URL is registered
When the user triggers a manual scan
Then a scan job is initiated for all registered URLs
And each URL's scan completes within 60 seconds
And a new score record with a current timestamp is stored in the data store
```

**Verification**: Automated integration test — trigger scan, assert record creation with timestamp within 60s.

---

### AC-04 — Score Dimensions Completeness (→ FR-03)

```gherkin
Given a scan is executed for "https://example-ota.com/hotels"
When the scan result is stored
Then the result record must contain non-null values for:
  Performance Score, SEO Score of lighthouse, Accessibility Score, Best Practices Score,
  LCP, INP, and CLS
```

**Verification**: Automated unit test — assert all fields exist and are non-null in a scan result fixture.

---

### AC-05 — Dashboard Score Display (→ FR-04)

```gherkin
Given scan records exist for all registered URLs
When the user opens the dashboard
Then the latest score for each URL is displayed within 3 seconds
And each URL row shows a status indicator:
  "pass" (green) if all dimension scores ≥ 90
  "warning" (yellow) if any score is between 50–89
  "fail" (red) if any score is < 50
```

**Verification**: Manual UI test with a stopwatch; automated Lighthouse performance test for load time.

---

### AC-06 — Historical Trend View (→ FR-05)

```gherkin
Given scan records exist for last 90 days for a registered URL
When the user selects that URL and sets the date range to the last 90 days
Then a time-series chart is rendered showing the daily score for each dimension
And a "Export CSV" button is present and downloads a valid CSV file upon click
```

**Verification**: Manual UI test — select date range and confirm chart renders; download CSV and validate column headers.

---

### AC-07 — Scheduled Scan Execution (→ FR-06)

```gherkin
Given the schedule is set to "daily at 00:00 UTC"
When the system clock reaches 00:00 UTC
Then a scan job is automatically enqueued and executed for all registered URLs
And a result notification email is delivered to the administrator within 15 minutes of job completion
```

**Verification**: Integration test with mocked scheduler — assert job enqueue at scheduled time; inspect email delivery log.

---

### AC-08 — Score Change Comparison (→ FR-07)

```gherkin
Given scan records exist for "2026-04-01" and "2026-05-01" for a target URL
When the user selects those two dates as baseline and comparison
Then a comparison table is displayed showing delta (Δ) per dimension
And dimensions with positive delta show "▲ +{n}" in green
And dimensions with negative delta show "▼ -{n}" in red
```

**Verification**: Manual UI test — select two dates with known score differences and confirm delta values and indicators.

---

### AC-09 — Comparison with Missing Record (→ FR-07)

```gherkin
Given no scan record exists for "2026-03-15"
When the user selects "2026-03-15" as a comparison date
Then the system displays the error: "No scan record found for the selected date"
And no comparison table is rendered
```

**Verification**: Manual UI test — select a date with no record and confirm error message.

---

### AC-10 — SEO Improvement Suggestion Display (→ FR-08)

```gherkin
Given a scan record exists for "https://example-ota.com/flights"
  And at least one Lighthouse audit has a score below 0.9
When the SEO specialist opens the "Suggestions" view for that URL
Then a ranked list of suggestions is displayed within 5 seconds
And each suggestion shows:
  Affected Dimension, Action Description, Lighthouse Audit ID,
  Estimated Score Impact (Δ), and Confidence Level (high / medium / low)
And the list is sorted in descending order of Estimated Score Impact
```

**Verification**: Automated integration test — seed a scan record with known failing audits, invoke the suggestion endpoint, assert ranking order and required fields; manual UI test for rendering latency.

---

### AC-11 — Suggestion Confidence Fallback (→ FR-08, NFR-08)

```gherkin
Given a failing Lighthouse audit "image-alt" exists in the latest scan
  And no historical scan record contains a prior remediation of "image-alt"
When the system generates suggestions for that URL
Then the suggestion for "image-alt" is still displayed
And its Confidence Level is set to "low"
And its Estimated Score Impact is displayed as "N/A"
```

**Verification**: Automated unit test — provide a fixture with zero historical precedent for the audit and assert the suggestion item's `confidence == "low"` and `estimated_impact == null`.
