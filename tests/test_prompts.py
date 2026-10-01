"""Prompts: structured parts + recipes, the structural intervention check, versions, rendering."""

from __future__ import annotations

import shutil

import pytest
from eng_helpers import REPO, read_table, write_table

from hiringaudit.config import load_jobs
from hiringaudit.prompts import (NEUTRALITY_PARAGRAPH, PSEUDONYMISATION_SENTENCE, check_intervention,
                                 check_recipe_intervention, load_library, paragraphs, render_forced_choice,
                                 render_independent, render_job_ad, render_principle, required_template_ids,
                                 validate_library, validate_prompts)

PROMPTS = REPO / "prompts"
LIB = load_library(PROMPTS)
JOBS = load_jobs(REPO / "stimuli" / "jobs.csv")


def _copy(tmp_path):
    d = tmp_path / "prompts"
    shutil.copytree(PROMPTS, d)
    return d


def _edit_recipes(d, fn):
    cols, rows = read_table(d / "prompt_recipes.csv")
    write_table(d / "prompt_recipes.csv", cols, fn(rows))


def test_repository_prompts_are_valid():
    assert validate_prompts(PROMPTS) == []
    assert sorted(LIB.templates) == sorted(required_template_ids())


@pytest.mark.parametrize("k", ["k1", "k2", "k3"])
@pytest.mark.parametrize("base,treated", [("baseline", "neutrality"), ("forced_choice", "forced_choice_neutrality")])
def test_neutrality_is_base_plus_exactly_one_part(k, base, treated):
    b, t = LIB.template(f"{base}_{k}"), LIB.template(f"{treated}_{k}")
    assert check_recipe_intervention(b, t) == []
    added = [s.part_id for s in t.steps if s.part_id not in {x.part_id for x in b.steps}]
    assert added == ["neutrality_paragraph"] and LIB.parts["neutrality_paragraph"].part_type == "intervention"
    assert check_intervention(b.user_template, t.user_template) == []
    extra = [p for p in paragraphs(t.user_template) if p not in paragraphs(b.user_template)]
    assert extra == [NEUTRALITY_PARAGRAPH]


def test_variants_differ_in_wording_but_share_output_part():
    ts = [LIB.template(f"baseline_{k}") for k in ("k1", "k2", "k3")]
    assert len({t.user_template for t in ts}) == 3
    assert {t.steps[-1].part_id for t in ts} == {"independent_output"}


def test_recipes_assemble_with_blank_lines_and_slots_below_their_header():
    t = LIB.template("baseline_k1")
    assert t.user_template.split("\n\n")[:3] == [
        "Please review the application below for the advertised position.",
        "JOB ADVERTISEMENT\n{JOB_AD}", "APPLICANT CV\n{CV}"]
    pp = LIB.template("principle_probe").user_template
    assert pp.startswith('{CONTEXT}\n\nConsider the following statement:\n"{ITEM}"\n\nRespond with a single JSON')


def _recipe(rows, cond, variant):
    return [r for r in rows if r["condition"] == cond and r["variant"] == variant]


def _insert(rows, cond, variant, before_step, part_id):
    """Insert a part before ``before_step`` of one recipe and renumber its steps."""
    out = []
    for r in rows:
        if r["condition"] == cond and r["variant"] == variant:
            n = int(r["step"])
            if n == before_step:
                out.append({**r, "part_id": part_id, "slot": ""})
            r = {**r, "step": str(n + 1 if n >= before_step else n)}
        out.append(r)
    return out


def _delete(rows, cond, variant, part_id):
    """Delete a part from one recipe and renumber its steps."""
    out, gone = [], None
    for r in rows:
        if r["condition"] == cond and r["variant"] == variant:
            if r["part_id"] == part_id:
                gone = int(r["step"])
                continue
            if gone is not None and int(r["step"]) > gone:
                r = {**r, "step": str(int(r["step"]) - 1)}
        out.append(r)
    return out


def _swap(rows, cond, variant, a, b):
    """Swap the steps a and b of one recipe."""
    rec = {int(r["step"]): r for r in _recipe(rows, cond, variant)}
    ca, cb = {k: rec[a][k] for k in ("part_id", "slot")}, {k: rec[b][k] for k in ("part_id", "slot")}
    rec[a].update(cb)
    rec[b].update(ca)
    return rows


@pytest.mark.parametrize("edit,expect", [
    # the intervention removed from a neutrality recipe
    (lambda rows: _delete(rows, "neutrality", "k2", "neutrality_paragraph"),
     "recipe neutrality_k2: must have exactly one step more"),
    # a second added part
    (lambda rows: _insert(rows, "neutrality", "k3", 2, "independent_intro_k3"),
     "recipe neutrality_k3: must have exactly one step more"),
    # a different part added instead of the intervention
    (lambda rows: [{**r, "part_id": "independent_task_k1"} if r["part_id"] == "neutrality_paragraph"
                   and r["condition"] == "neutrality" and r["variant"] == "k1" else r for r in rows],
     "is not an intervention part"),
    # the intervention moved away from the output instructions
    (lambda rows: _swap(rows, "neutrality", "k1", 7, 8), "immediately before the output instructions"),
    # a baseline recipe that contains the intervention
    (lambda rows: _insert(rows, "baseline", "k2", 7, "neutrality_paragraph"), "not a neutrality condition"),
    # a slot that is not below its header
    (lambda rows: _swap(rows, "baseline", "k3", 5, 6), "slot CV must directly follow a section_header"),
    # a part of another task or variant
    (lambda rows: [{**r, "part_id": "forced_choice_intro_k1"} if (r["condition"], r["variant"], r["step"]) ==
                   ("baseline", "k1", "2") else r for r in rows], "is written for task forced_choice"),
    # a missing recipe
    (lambda rows: [r for r in rows if not (r["condition"] == "forced_choice" and r["variant"] == "k2")],
     "recipe forced_choice_k2 is missing"),
])
def test_structural_validator_catches_broken_recipes(tmp_path, edit, expect):
    d = _copy(tmp_path)
    _edit_recipes(d, edit)
    probs = validate_prompts(d)
    assert any(expect in p for p in probs), probs


def test_validator_checks_the_parts(tmp_path):
    d = _copy(tmp_path)
    cols, rows = read_table(d / "prompt_parts.csv")
    for r in rows:
        if r["part_id"] == "neutrality_paragraph":
            r["text"] = r["text"].replace("job-relevant qualifications", "relevant qualifications")
        if r["part_id"] == "forced_choice_task_k3":
            r["text"] += " Consider {nationality}."
        if r["part_id"] == "system":
            r["text"] = r["text"].replace(PSEUDONYMISATION_SENTENCE, "")
    write_table(d / "prompt_parts.csv", cols, rows)
    probs = "\n".join(validate_prompts(d))
    assert "canonical neutrality paragraph" in probs and "unknown placeholder(s) ['nationality']" in probs
    assert "pseudonymisation sentence" in probs


def test_system_prompt_and_versions():
    assert PSEUDONYMISATION_SENTENCE in LIB.system_text
    assert LIB.system_version == f"system@sha256:{LIB.system_sha256}" and len(LIB.system_sha256) == 64
    t = LIB.template("forced_choice_k2")
    assert t.version == f"forced_choice_k2@sha256:{t.sha256}" and t.system_text == LIB.system_text
    assert "jailbreak" not in " ".join(LIB.template(f"forced_choice_{k}").user_template for k in ("k1", "k2", "k3"))
    assert validate_library(LIB) == []


def test_job_ad_is_located_in_the_cv_base_city():
    raw = JOBS["software_developer"]
    with pytest.raises(ValueError, match="not localized"):
        render_job_ad(raw)
    a, b = render_job_ad(raw.localize("Doha", "Qatar")), render_job_ad(raw.localize("Amman", "Jordan"))
    assert "Location: Doha, Qatar" in a and "office in Doha" in a and "Doha" not in b
    diff = [(x, y) for x, y in zip(a.split("\n"), b.split("\n")) if x != y]
    assert all("Doha" in x and "Amman" in y for x, y in diff) and len(a.split("\n")) == len(b.split("\n"))
    for job in JOBS.values():                     # only the location is filled in
        assert job.localize("Doha", "Qatar").requirements == job.requirements


def test_rendering_fills_every_slot():
    job = JOBS["software_developer"].localize("Doha", "Qatar")
    ad = render_job_ad(job)
    assert "Fluent English (C1 or higher)" in ad and "German" not in ad
    for k in ("k1", "k2", "k3"):
        out = render_independent(LIB.template(f"baseline_{k}"), job, "CV TEXT\n")
        assert "{" not in out.replace(ad, "") and "CV TEXT" in out and "APPLICANT CV\nCV TEXT" in out
        fc = render_forced_choice(LIB.template(f"forced_choice_{k}"), job, "CV-ONE", "CV-TWO")
        assert fc.index("CANDIDATE A\nCV-ONE") < fc.index("CANDIDATE B\nCV-TWO")
    pr = render_principle(LIB.template("principle_probe"), "CONTEXT LINE", "A statement.")
    assert pr.startswith("CONTEXT LINE\n\n") and '"A statement."' in pr and '"answer"' in pr
    msgs = LIB.template("baseline_k1").render({"JOB_AD": ad, "CV": "CV TEXT"})
    assert [m["role"] for m in msgs] == ["system", "user"] and msgs[0]["content"] == LIB.system_text
