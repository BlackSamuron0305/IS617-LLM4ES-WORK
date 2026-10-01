"""Download country-level covariates for hypothesis H1d from the World Bank API.

Writes config/country_covariates.csv. Values are fetched, never typed in:
this script is the only way the file should be produced. Re-running it on a
later date can return revised WDI values, so the file is frozen (committed)
before main-study data collection and the retrieval date is stored per row.

Rule (research/hypotheses.md, H1d): GDP per capita, PPP, constant international
dollars (NY.GDP.PCAP.PP.KD), reference year 2022. If 2022 is missing, use the
most recent value in 2015-2021 and flag it. If none, leave empty and flag
`excluded`.

Usage:
    python scripts/fetch_country_covariates.py
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDICATOR = "NY.GDP.PCAP.PP.KD"
REFERENCE_YEAR = 2022
FALLBACK_YEARS = range(2021, 2014, -1)  # most recent first
API = "https://api.worldbank.org/v2"


def get_json(url: str) -> list:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_indicator(codes: list[str]) -> dict[str, dict[int, float]]:
    url = (
        f"{API}/country/{';'.join(codes)}/indicator/{INDICATOR}"
        f"?date=2015:{REFERENCE_YEAR}&format=json&per_page=1000"
    )
    payload = get_json(url)
    if len(payload) < 2 or payload[1] is None:
        raise RuntimeError(f"Unexpected World Bank response: {payload[:1]}")
    out: dict[str, dict[int, float]] = {c: {} for c in codes}
    for row in payload[1]:
        if row["value"] is not None:
            out[row["countryiso3code"]][int(row["date"])] = float(row["value"])
    return out


def fetch_country_meta(codes: list[str]) -> dict[str, dict[str, str]]:
    """Income group and World Bank region (current classification edition)."""
    payload = get_json(f"{API}/country/{';'.join(codes)}?format=json&per_page=100")
    return {
        row["id"]: {"income_group": row["incomeLevel"]["value"], "wb_region": row["region"]["value"].strip()}
        for row in payload[1]
    }


def main() -> int:
    with open(ROOT / "stimuli" / "nationalities.csv", encoding="utf-8", newline="") as fh:
        codes = [r["code"] for r in csv.DictReader(fh) if r["code"] != "NONE"]

    series = fetch_indicator(codes)
    meta = fetch_country_meta(codes)
    retrieved = dt.date.today().isoformat()

    rows = []
    for code in codes:
        values = series.get(code, {})
        if REFERENCE_YEAR in values:
            year, value, flag = REFERENCE_YEAR, values[REFERENCE_YEAR], "reference_year"
        else:
            year = next((y for y in FALLBACK_YEARS if y in values), None)
            value = values[year] if year is not None else None
            flag = "fallback" if year is not None else "excluded"
        rows.append(
            {
                "code": code,
                "gdp_pc_ppp_const": "" if value is None else f"{value:.2f}",
                "gdp_year": "" if year is None else year,
                "gdp_flag": flag,
                "income_group": meta.get(code, {}).get("income_group", ""),
                "wb_region": meta.get(code, {}).get("wb_region", ""),
                # Sensitivity indicator for H1d (adversarial review M9): the
                # World Bank's regional assignment, not a racial classification.
                "wb_sub_saharan": int(meta.get(code, {}).get("wb_region", "") == "Sub-Saharan Africa"),
                "source": f"World Bank WDI API, indicator {INDICATOR}; income group and region from World Bank country API",
                "retrieval_date": retrieved,
            }
        )

    out_path = ROOT / "config" / "country_covariates.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    flagged = [r["code"] for r in rows if r["gdp_flag"] != "reference_year"]
    print(f"Wrote {out_path.relative_to(ROOT)} ({len(rows)} rows); non-reference-year: {flagged or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
