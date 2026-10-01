"""CV building blocks: the curated component tables in ``stimuli/building_blocks/``.

They are the INPUT of ``scripts/build_cv_table.py`` (``build_table.py``), which
composed the 48 base CVs of ``stimuli/cvs.csv``, and the reference of the
title-bullet coherence check of ``validate-stimuli``. After the build,
``stimuli/cvs.csv`` is the source of truth; the experiment runtime never reads
these tables (except ``institutions.csv``, the validator's whitelist, see
``stimuli/setting.py``). Row order matters: the builder draws from every list in
table order with a fixed seed, so reordering rows changes a rebuilt table.

Files (one entity per row; lists " | "-separated):

    build_settings.csv   setting, value, description: seed, reference_date,
                         availability, languages (design constants), school
    cv_slots.csv         one row per base CV: cv_id, occupation, position,
                         qualification_tier, pilot, fc_pair (same-tier pair that
                         shares a base country), base_country
    roles.csv            occupation, kind (junior | mid | senior | unrelated),
                         title, profile_phrase and employers (unrelated roles only)
    bullets.csv          occupation, bullet_set, bullet; bullet_set = core (every
                         title of the occupation), senior (senior titles in
                         addition) or the title of an unrelated role
    employers.csv        occupation, employer (employers of the occupation's own titles)
    achievements.csv     occupation, qualification_tier, achievement
    profiles.csv         occupation, qualification_tier, profile ({experience},
                         {unrelated} placeholders)
    skills.csv           occupation, kind (required | nice | tools), skill
    qualifications.csv   occupation, level (advanced | relevant), degree, years,
                         institution_kind, preceding_bachelor (a master's: the
                         possible preceding bachelor's degrees)
    certifications.csv   occupation, kind (required | optional), name, since
    institutions.csv     base_country, institution_kind, institution

``load_building_blocks`` returns them as one nested dict (the structure the
builder and the coherence check use).
"""

from __future__ import annotations

from pathlib import Path

from .. import csvio

TIERS = ("strong", "adequate", "borderline")
TITLE_LEVELS = ("junior", "mid", "senior")
FILES = ("build_settings.csv", "cv_slots.csv", "roles.csv", "bullets.csv", "employers.csv", "achievements.csv",
         "profiles.csv", "skills.csv", "qualifications.csv", "certifications.csv", "institutions.csv")


class BuildingBlockError(ValueError):
    pass


def _rows(d: Path, name: str, columns: tuple[str, ...]) -> list[dict[str, str]]:
    rows = csvio.read_rows(d / name, columns, allowed=columns)
    return [{k: csvio.text(v) for k, v in r.items()} for r in rows]


def load_building_blocks(blocks_dir: str | Path) -> dict:
    """All building blocks as one dict: build settings, the CV slots (tier sequence,
    pilot positions, forced-choice pairs, base-country allocation) and one pool per
    occupation (``occupations``)."""
    d = Path(blocks_dir)
    settings = {r["setting"]: r["value"] for r in _rows(d, "build_settings.csv", ("setting", "value", "description"))}
    need = {"seed", "reference_date", "availability", "languages", "school"}
    if set(settings) != need:
        raise BuildingBlockError(f"build_settings.csv must define exactly {sorted(need)}, got {sorted(settings)}")

    slots = _rows(d, "cv_slots.csv", ("cv_id", "occupation", "position", "qualification_tier", "pilot", "fc_pair",
                                      "base_country"))
    occupations: dict[str, dict] = {}
    by_occ: dict[str, list[dict]] = {}
    for s in slots:
        at = csvio.where(d / "cv_slots.csv", s["cv_id"])
        s["position"] = csvio.integer(s["position"], at)
        s["fc_pair"] = csvio.integer(s["fc_pair"], at)
        s["pilot"] = csvio.boolean(s["pilot"], at)
        if s["qualification_tier"] not in TIERS:
            raise BuildingBlockError(f"{at}: unknown tier {s['qualification_tier']!r}")
        by_occ.setdefault(s["occupation"], []).append(s)
    sequences = set()
    for occ, ss in by_occ.items():
        ss.sort(key=lambda s: s["position"])
        if [s["position"] for s in ss] != list(range(1, len(ss) + 1)):
            raise BuildingBlockError(f"cv_slots.csv: positions of {occ} must be 1..n")
        short = ss[0]["cv_id"].rsplit("_", 1)[0]
        if any(s["cv_id"] != f"{short}_{s['position']:02d}" for s in ss):
            raise BuildingBlockError(f"cv_slots.csv: cv_ids of {occ} must be <short>_<position:02d>")
        sequences.add(tuple((s["qualification_tier"], s["pilot"], s["fc_pair"]) for s in ss))
        occupations[occ] = {"short": short}
    if len(sequences) != 1:
        raise BuildingBlockError("cv_slots.csv: every occupation must have the same tier, pilot and fc_pair per "
                                 "position")
    seq = next(iter(sequences))
    pair_ids = sorted({p for _, _, p in seq})
    fc_pairs = [[i + 1 for i, (_, _, p) in enumerate(seq) if p == k] for k in pair_ids]
    allocation = {}
    for occ, ss in by_occ.items():
        codes = []
        for k in pair_ids:
            c = {s["base_country"] for s in ss if s["fc_pair"] == k}
            if len(c) != 1:
                raise BuildingBlockError(f"cv_slots.csv: {occ} fc_pair {k} must share one base country, got {c}")
            codes.append(c.pop())
        allocation[occ] = codes

    def put(group: dict, key: str, value, name: str) -> None:
        if key not in group:
            raise BuildingBlockError(f"{name}: unknown value {key!r} (expected one of {sorted(group)})")
        group[key].append(value)

    def per_occ(name: str, columns: tuple[str, ...]) -> list[dict[str, str]]:
        rows = _rows(d, name, columns)
        unknown = sorted({r["occupation"] for r in rows} - set(occupations))
        if unknown:
            raise BuildingBlockError(f"{name}: occupations not in cv_slots.csv: {unknown}")
        return rows

    for occ, pool in occupations.items():
        pool.update({"titles": {lvl: [] for lvl in ("senior", "mid", "junior")}, "employers": [],
                     "bullets": {"core": [], "senior": []}, "achievements": {t: [] for t in TIERS},
                     "unrelated_roles": [], "skills": {"required": [], "nice": [], "tools": []},
                     "qualifications": {"advanced": [], "relevant": []},
                     "certifications": {"required": [], "optional": []}, "profiles": {t: [] for t in TIERS}})

    unrelated: dict[tuple[str, str], dict] = {}
    for r in per_occ("roles.csv", ("occupation", "kind", "title", "profile_phrase", "employers")):
        pool = occupations[r["occupation"]]
        if r["kind"] in TITLE_LEVELS:
            if r["profile_phrase"] or r["employers"]:
                raise BuildingBlockError(f"roles.csv {r['title']!r}: profile_phrase and employers are for unrelated "
                                         f"roles only (occupation titles use employers.csv)")
            put(pool["titles"], r["kind"], r["title"], "roles.csv")
        elif r["kind"] == "unrelated":
            role = {"title": r["title"], "as": r["profile_phrase"], "employers": csvio.items(r["employers"]),
                    "bullets": []}
            if not role["as"] or not role["employers"]:
                raise BuildingBlockError(f"roles.csv {r['title']!r}: an unrelated role needs profile_phrase and "
                                         f"employers")
            pool["unrelated_roles"].append(role)
            unrelated[(r["occupation"], r["title"])] = role
        else:
            raise BuildingBlockError(f"roles.csv {r['title']!r}: unknown kind {r['kind']!r}")
    for r in per_occ("bullets.csv", ("occupation", "bullet_set", "bullet")):
        pool = occupations[r["occupation"]]
        if r["bullet_set"] in ("core", "senior"):
            pool["bullets"][r["bullet_set"]].append(r["bullet"])
        elif (r["occupation"], r["bullet_set"]) in unrelated:
            unrelated[(r["occupation"], r["bullet_set"])]["bullets"].append(r["bullet"])
        else:
            raise BuildingBlockError(f"bullets.csv: bullet_set {r['bullet_set']!r} is neither core, senior nor an "
                                     f"unrelated role of {r['occupation']}")
    for r in per_occ("employers.csv", ("occupation", "employer")):
        occupations[r["occupation"]]["employers"].append(r["employer"])
    for name, col, key in (("achievements.csv", "achievement", "achievements"), ("profiles.csv", "profile", "profiles")):
        for r in per_occ(name, ("occupation", "qualification_tier", col)):
            put(occupations[r["occupation"]][key], r["qualification_tier"], r[col], name)
    for r in per_occ("skills.csv", ("occupation", "kind", "skill")):
        put(occupations[r["occupation"]]["skills"], r["kind"], r["skill"], "skills.csv")
    for r in per_occ("qualifications.csv", ("occupation", "level", "degree", "years", "institution_kind",
                                            "preceding_bachelor")):
        q = {"degree": r["degree"], "years": csvio.integer(r["years"], csvio.where(d / "qualifications.csv", r["degree"])),
             "kind": r["institution_kind"]}
        if r["preceding_bachelor"]:
            q["bachelor"] = csvio.items(r["preceding_bachelor"])
        put(occupations[r["occupation"]]["qualifications"], r["level"], q, "qualifications.csv")
    for r in per_occ("certifications.csv", ("occupation", "kind", "name", "since")):
        c = {"name": r["name"]}
        if r["since"]:
            c["since"] = csvio.integer(r["since"], csvio.where(d / "certifications.csv", r["name"]))
        put(occupations[r["occupation"]]["certifications"], r["kind"], c, "certifications.csv")

    return {
        "seed": csvio.integer(settings["seed"], "build_settings.csv seed"),
        "reference_date": settings["reference_date"],
        "n_per_occupation": len(seq),
        "tier_sequence": [t for t, _, _ in seq],
        "pilot_positions": [i + 1 for i, (_, p, _) in enumerate(seq) if p],
        "fc_pairs": fc_pairs,
        "base_country_allocation": allocation,
        "held_constant": {"availability": settings["availability"], "languages": settings["languages"]},
        "school": settings["school"],
        "occupations": occupations,
    }
