"""Render a CV row with a nationality row into plain text, with ONE fixed template.

This happens when a prompt is built: prompt = job ad + render(cv_row,
nationality_row, clone_type). The ``Nationality:`` line is the only thing that
depends on the nationality row, so the clones of a CV are identical by
construction:

* counterfactual clone: ``Nationality: <demonym>`` at the fixed position
  (between Location and Work authorization);
* NONE (control): the whole Nationality line is omitted, nothing else changes;
* positive control: the NONE clone with the CV's ``positive_control_lines``
  removed: EVERY qualification line that satisfies the job ad's designated
  must-have (e.g. both the M.Sc. and the preceding B.Sc.).

Personal-details order (fixed): Applicant reference, Location, Nationality, Work
authorization, Driving licence, Availability, Languages; then Profile, Key
achievements, Experience, Education, Skills, Certifications.
"""

from __future__ import annotations

from pathlib import Path

from ..utils import normalize_newlines

NATIONALITY_PLACEHOLDER_LINE = "{{NATIONALITY_LINE}}\n"
NATIONALITY_PREFIX = "Nationality: "
COUNTERFACTUAL = "counterfactual"
POSITIVE_CONTROL = "positive_control"
CONTROL_CODE = "NONE"


def stimulus_id(cv_id: str, code: str, clone_type: str = COUNTERFACTUAL) -> str:
    return f"{cv_id}__{code}__pc" if clone_type == POSITIVE_CONTROL else f"{cv_id}__{code}"


def load_template(path: str | Path) -> str:
    text = normalize_newlines(Path(path).read_text(encoding="utf-8"))
    if text.count(NATIONALITY_PLACEHOLDER_LINE) != 1:
        raise ValueError(f"template {path} must contain exactly one line consisting of {{{{NATIONALITY_LINE}}}}")
    return text


def education_line(e: dict) -> str:
    if e.get("institution"):
        return f"{e['start']} - {e['end']} | {e['degree']} | {e['institution']}"
    return f"{e['end']} | {e['degree']}"


def _experience_block(cv: dict) -> str:
    blocks = []
    for job in cv["experience"]:
        lines = [f"{job['start']} - {job['end']} | {job['title']} | {job['employer']}, {job['city']}"]
        lines += [f"- {b}" for b in job["bullets"]]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _achievements_block(cv: dict) -> str:
    if not cv.get("achievements"):
        return "None listed"
    return "\n".join(f"- {a}" for a in cv["achievements"])


def _certifications_block(cv: dict) -> str:
    if not cv["certifications"]:
        return "None listed"
    return "\n".join(f"- {c['name']} ({c['year']})" if c.get("year") else f"- {c['name']}"
                     for c in cv["certifications"])


def render_cv(cv: dict, demonym: str | None, template: str) -> str:
    """Render ``cv`` with the given demonym (``None`` = omit the Nationality line)."""
    if demonym is None:
        text = template.replace(NATIONALITY_PLACEHOLDER_LINE, "", 1)
    else:
        text = template.replace(NATIONALITY_PLACEHOLDER_LINE, f"{NATIONALITY_PREFIX}{demonym}\n", 1)
    values = {
        "APPLICANT_REFERENCE": cv["applicant_reference"],
        "LOCATION": cv["location"],
        "WORK_AUTHORIZATION": cv["work_authorization"],
        "DRIVING_LICENCE": cv["driving_licence"],
        "AVAILABILITY": cv["availability"],
        "LANGUAGES": cv["languages"],
        "PROFILE": cv["profile"],
        "ACHIEVEMENTS": _achievements_block(cv),
        "EXPERIENCE": _experience_block(cv),
        "EDUCATION": "\n".join(education_line(e) for e in cv["education"]),
        "SKILLS": ", ".join(cv["skills"]),
        "CERTIFICATIONS": _certifications_block(cv),
    }
    for key, val in values.items():
        text = text.replace("{{" + key + "}}", val)
    if "{{" in text or "}}" in text:
        raise ValueError(f"unfilled placeholder in rendered CV {cv.get('cv_id')}")
    return text


def remove_line(text: str, line: str) -> str:
    """Remove exactly one occurrence of ``line`` (a whole line) from ``text``."""
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l == line]
    if len(idx) != 1:
        raise ValueError(f"expected exactly one line {line!r}, found {len(idx)}")
    return "\n".join(lines[: idx[0]] + lines[idx[0] + 1:])


def remove_lines(text: str, lines: list[str]) -> str:
    """Remove each of ``lines`` (whole lines, each occurring exactly once)."""
    if not lines:
        raise ValueError("no positive_control_lines to remove")
    for line in lines:
        text = remove_line(text, line)
    return text


def render_clone(cv: dict, demonym: str | None, clone_type: str, template: str) -> str:
    """The CV text a model sees for (cv row, nationality row, clone type)."""
    if clone_type == POSITIVE_CONTROL:
        return remove_lines(render_cv(cv, None, template), cv["positive_control_lines"])
    if clone_type != COUNTERFACTUAL:
        raise ValueError(f"unknown clone_type {clone_type!r}")
    return render_cv(cv, demonym, template)
