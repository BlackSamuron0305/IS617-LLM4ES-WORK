"""The two stimulus tables: ``stimuli/cvs.csv`` and ``stimuli/nationalities.csv``.

Both are plain UTF-8 CSV files, readable and editable in Excel or an IDE. They
are the source of truth for the stimuli: every prompt combines one CV row with
one nationality row at prompt-build time (``stimuli/render.py``).

cvs.csv (one row per base CV; no nationality column)
    cv_id, occupation, qualification_tier, pilot, base_country, base_city,
    applicant_reference, reference_date, relevant_experience_months,
    total_experience_months, positive_control_education, location,
    work_authorization, driving_licence, availability, languages, profile,
    achievement<i>                            (key achievements)
    exp<i>_title, exp<i>_employer, exp<i>_city, exp<i>_start, exp<i>_end,
    exp<i>_relevant, exp<i>_bullets          (exp1 = most recent job)
    edu<i>_degree, edu<i>_institution, edu<i>_start, edu<i>_end
    skills, cert<i>_name, cert<i>_year
  List cells (bullets, skills, positive_control_education) separate items with
  " | ". Empty cells mean "no such entry". Dates are MM/YYYY or "present";
  months are whole numbers. ``base_country`` (ISO3 code of a row of
  nationalities.csv) and ``base_city`` set the CV in one Arab League country
  (see stimuli/setting.py). ``positive_control_education`` names the education
  entries (``edu1``, ``edu2``, ...) whose rendered lines the positive control
  removes (every qualification that satisfies the job ad's designated
  must-have); the loader turns them into ``positive_control_lines``.

nationalities.csv (one row per nationality condition)
    code, country, demonym, group, subregion, arab_league_joined,
    arab_identity_contested, note
  The NONE row (control) has no country and no demonym. DEU is the reference.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from .config import Nationality, NationalitySet
from .csvio import LIST_SEP, TableError

REFERENCE_CODE = "DEU"
CONTROL_CODE = "NONE"

CV_META_COLUMNS = ("cv_id", "occupation", "qualification_tier", "pilot", "base_country", "base_city",
                   "applicant_reference", "reference_date", "relevant_experience_months",
                   "total_experience_months", "positive_control_education")
CV_PERSONAL_COLUMNS = ("location", "work_authorization", "driving_licence", "availability", "languages")
EXP_FIELDS = ("title", "employer", "city", "start", "end", "relevant", "bullets")
EDU_FIELDS = ("degree", "institution", "start", "end")
CERT_FIELDS = ("name", "year")
NATIONALITY_COLUMNS = ("code", "country", "demonym", "group", "subregion", "arab_league_joined",
                       "arab_identity_contested", "note")
NATIONALITY_GROUPS = ("arab", "benchmark", "placebo", "control")

_TRUE = {"true", "1", "yes"}
_FALSE = {"false", "0", "no"}


def _bool(value: str, where: str) -> bool:
    v = (value or "").strip().lower()
    if v in _TRUE:
        return True
    if v in _FALSE:
        return False
    raise TableError(f"{where}: expected true/false, got {value!r}")


def _read_rows(path: str | Path) -> tuple[list[str], list[dict]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = [dict(r) for r in reader]
        return list(reader.fieldnames or []), rows


def _indices(columns: list[str], prefix: str) -> list[int]:
    return sorted({int(m.group(1)) for c in columns for m in [re.match(rf"^{prefix}(\d+)_", c)] if m})


def _achievement_indices(columns: list[str]) -> list[int]:
    return sorted({int(m.group(1)) for c in columns for m in [re.match(r"^achievement(\d+)$", c)] if m})


# --------------------------------------------------------------------------- #
# nationalities.csv
# --------------------------------------------------------------------------- #
def load_nationalities(path: str | Path) -> NationalitySet:
    columns, rows = _read_rows(path)
    missing = [c for c in NATIONALITY_COLUMNS if c not in columns]
    if missing:
        raise TableError(f"{path}: missing columns {missing}")
    conds = []
    for i, r in enumerate(rows, start=2):
        where = f"{Path(path).name} line {i}"
        joined = (r["arab_league_joined"] or "").strip()
        conds.append(Nationality(
            code=r["code"].strip(), country=r["country"].strip() or None, demonym=r["demonym"] or None,
            group=r["group"].strip(), subregion=r["subregion"].strip(),
            arab_identity_contested=_bool(r["arab_identity_contested"], where),
            arab_league_joined=int(joined) if joined else None, note=(r.get("note") or "").strip()))
    codes = [c.code for c in conds]
    if len(codes) != len(set(codes)):
        dup = sorted({c for c in codes if codes.count(c) > 1})
        raise TableError(f"{path}: duplicate nationality codes {dup}")
    if REFERENCE_CODE not in codes:
        raise TableError(f"{path}: the reference nationality {REFERENCE_CODE} is missing")
    return NationalitySet(reference=REFERENCE_CODE, conditions=tuple(conds))


# --------------------------------------------------------------------------- #
# cvs.csv
# --------------------------------------------------------------------------- #
def row_to_cv(row: dict, columns: list[str]) -> dict:
    """One wide table row -> the structured CV dict used by the renderer."""
    where = f"cvs.csv row {row.get('cv_id')!r}"
    cv = {k: (row.get(k) or "").strip() for k in CV_META_COLUMNS + CV_PERSONAL_COLUMNS}
    cv["profile"] = (row.get("profile") or "").strip()
    cv["pilot"] = _bool(row.get("pilot", ""), where)
    cv["positive_control_education"] = [x.strip() for x in cv["positive_control_education"].split(LIST_SEP.strip())
                                        if x.strip()]
    cv["achievements"] = [a for a in ((row.get(f"achievement{i}") or "").strip()
                                      for i in _achievement_indices(columns)) if a]
    for k in ("relevant_experience_months", "total_experience_months"):
        try:
            cv[k] = int(cv[k])
        except ValueError as e:
            raise TableError(f"{where}: {k} must be a whole number") from e
    cv["experience"] = []
    for i in _indices(columns, "exp"):
        cells = {f: (row.get(f"exp{i}_{f}") or "").strip() for f in EXP_FIELDS}
        if not any(cells.values()):
            continue
        cv["experience"].append({
            "title": cells["title"], "employer": cells["employer"], "city": cells["city"],
            "start": cells["start"], "end": cells["end"], "relevant": _bool(cells["relevant"], f"{where} exp{i}"),
            "bullets": [b.strip() for b in cells["bullets"].split(LIST_SEP.strip()) if b.strip()]})
    cv["education"] = []
    edu_by_ref = {}
    for i in _indices(columns, "edu"):
        cells = {f: (row.get(f"edu{i}_{f}") or "").strip() for f in EDU_FIELDS}
        if not any(cells.values()):
            continue
        entry = {"degree": cells["degree"], "institution": cells["institution"] or None,
                 "start": cells["start"] or None, "end": cells["end"]}
        cv["education"].append(entry)
        edu_by_ref[f"edu{i}"] = entry
    unknown = [r for r in cv["positive_control_education"] if r not in edu_by_ref]
    if unknown:
        raise TableError(f"{where}: positive_control_education names {unknown}, which are not filled-in "
                         f"education entries (edu1, edu2, ...)")
    from .stimuli.render import education_line  # local import avoids a cycle

    cv["positive_control_lines"] = [education_line(edu_by_ref[r]) for r in cv["positive_control_education"]]
    cv["skills"] = [s.strip() for s in (row.get("skills") or "").split(LIST_SEP.strip()) if s.strip()]
    cv["certifications"] = []
    for i in _indices(columns, "cert"):
        name = (row.get(f"cert{i}_name") or "").strip()
        year = (row.get(f"cert{i}_year") or "").strip()
        if name:
            cv["certifications"].append({"name": name, "year": int(year) if year else None})
    return cv


def load_cv_table(path: str | Path) -> list[dict]:
    columns, rows = _read_rows(path)
    missing = [c for c in (*CV_META_COLUMNS, *CV_PERSONAL_COLUMNS, "profile", "skills") if c not in columns]
    if missing:
        raise TableError(f"{path}: missing columns {missing}")
    return [row_to_cv(r, columns) for r in rows]


def cv_to_row(cv: dict, n_exp: int, n_edu: int, n_cert: int, n_ach: int = 0) -> dict:
    row = {k: cv.get(k, "") for k in CV_META_COLUMNS + CV_PERSONAL_COLUMNS}
    row["pilot"] = "true" if cv.get("pilot") else "false"
    row["positive_control_education"] = LIST_SEP.join(cv.get("positive_control_education") or [])
    row["profile"] = cv["profile"]
    for i in range(n_ach):
        row[f"achievement{i + 1}"] = cv["achievements"][i] if i < len(cv.get("achievements", [])) else ""
    for i in range(n_exp):
        j = cv["experience"][i] if i < len(cv["experience"]) else None
        for f in EXP_FIELDS:
            if j is None:
                v = ""
            elif f == "bullets":
                v = LIST_SEP.join(j["bullets"])
            elif f == "relevant":
                v = "true" if j.get("relevant", True) else "false"
            else:
                v = j[f]
            row[f"exp{i + 1}_{f}"] = v
    for i in range(n_edu):
        e = cv["education"][i] if i < len(cv["education"]) else None
        for f in EDU_FIELDS:
            row[f"edu{i + 1}_{f}"] = "" if e is None or e.get(f) is None else e[f]
    row["skills"] = LIST_SEP.join(cv["skills"])
    for i in range(n_cert):
        c = cv["certifications"][i] if i < len(cv["certifications"]) else None
        row[f"cert{i + 1}_name"] = "" if c is None else c["name"]
        row[f"cert{i + 1}_year"] = "" if c is None or c.get("year") is None else c["year"]
    return row


def cv_table_columns(n_exp: int, n_edu: int, n_cert: int, n_ach: int = 0) -> list[str]:
    cols = list(CV_META_COLUMNS + CV_PERSONAL_COLUMNS) + ["profile"]
    cols += [f"achievement{i}" for i in range(1, n_ach + 1)]
    cols += [f"exp{i}_{f}" for i in range(1, n_exp + 1) for f in EXP_FIELDS]
    cols += [f"edu{i}_{f}" for i in range(1, n_edu + 1) for f in EDU_FIELDS]
    cols += ["skills"] + [f"cert{i}_{f}" for i in range(1, n_cert + 1) for f in CERT_FIELDS]
    return cols


def write_cv_table(cvs: list[dict], path: str | Path) -> None:
    n_exp = max(len(c["experience"]) for c in cvs)
    n_edu = max(len(c["education"]) for c in cvs)
    n_cert = max(1, max(len(c["certifications"]) for c in cvs))
    n_ach = max(len(c.get("achievements", [])) for c in cvs)
    cols = cv_table_columns(n_exp, n_edu, n_cert, n_ach)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for cv in cvs:
            w.writerow(cv_to_row(cv, n_exp, n_edu, n_cert, n_ach))
