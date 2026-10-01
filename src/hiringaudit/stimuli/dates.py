"""Date helpers shared by the table builder and the validator."""

from __future__ import annotations


def month_index(year: int, month: int) -> int:
    return year * 12 + (month - 1)


def fmt_month(idx: int) -> str:
    return f"{idx % 12 + 1:02d}/{idx // 12}"


def parse_month(s: str, present: int) -> int:
    """'MM/YYYY' or 'present' -> month index."""
    if s == "present":
        return present
    mm, yyyy = s.split("/")
    return month_index(int(yyyy), int(mm))


def reference_month(reference_date: str) -> int:
    y, m = (int(x) for x in reference_date.split("-"))
    return month_index(y, m)


def job_months(job: dict, present: int) -> int:
    return parse_month(job["end"], present) - parse_month(job["start"], present)


def experience_months(cv: dict, reference_date: str) -> tuple[int, int]:
    """(relevant months, total months) computed from the job dates."""
    present = reference_month(reference_date)
    rel = sum(job_months(j, present) for j in cv["experience"] if j.get("relevant", True))
    tot = sum(job_months(j, present) for j in cv["experience"])
    return rel, tot


def format_duration(months: int) -> str:
    """'8 months', '1 year', '4 years' (whole years, rounded down)."""
    if months < 12:
        return f"{months} months"
    years = months // 12
    return "1 year" if years == 1 else f"{years} years"
