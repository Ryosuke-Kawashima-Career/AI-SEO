# Lighthouse Baseline Bands

> **Source**: `data/SEO_Page Score.xlsx` (sheet `NAP_SEO04_2026`, Mobile column, March 2026 reference scan).
> **Used by**: `backend/tests/test_live_lighthouse.py` (opt-in live integration test).

## Reference scores (Mobile)

| URL | Excel row | Performance | Accessibility | Best Practices | SEO |
|---|---|---|---|---|---|
| `https://adventure.inc/` | Total top | 95 | 97 | 92 | 100 |
| `https://adventure.inc/about-us` | — (no reference) | — | — | — | — |
| `https://adventure.inc/hotels` | Hotel top | 95 | 97 | 92 | 100 |
| `https://adventure.inc/hotels/tokyo/tokyo-lp-house-1444228` | Detail - SEO | 84 | 96 | 96 | 100 |

## Acceptance bands (lower bound)

PSI scores fluctuate run-to-run (especially Performance, which depends on lab CPU and network conditions). The acceptance bands below are intentionally **wide** so the live test passes consistently while still catching regressions like a category dropping by 30+ points.

| URL | Performance ≥ | Accessibility ≥ | Best Practices ≥ | SEO ≥ |
|---|---|---|---|---|
| `https://adventure.inc/` | 50 | 80 | 70 | 70 |
| `https://adventure.inc/about-us` | 30 | 70 | 60 | 60 |
| `https://adventure.inc/hotels` | 50 | 80 | 70 | 70 |
| `https://adventure.inc/hotels/tokyo/tokyo-lp-house-1444228` | 40 | 80 | 70 | 60 |

## Update protocol

When the target list or expected baselines change:

1. Edit `data/SEO_Page Score.xlsx` and re-export the reference table here.
2. Update `EXPECTED_BANDS` in `backend/tests/test_live_lighthouse.py`.
3. Re-run `RUN_LIVE_LIGHTHOUSE=1 pytest tests/test_live_lighthouse.py -v` and confirm all URLs pass.
