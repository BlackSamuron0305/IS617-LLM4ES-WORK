"""Prompt / trial snapshot used to prove that a structural refactor changes no behaviour.

``compute_run_snapshot`` renders the full system + user message of EVERY trial of a
loaded experiment and reduces them to digests (plus one row per trial for small
runs); ``compute_stimulus_snapshot`` does the same for every rendered job ad and CV
clone. ``tests/fixtures/prompt_snapshot.jsonl`` holds the values captured on
2026-10-01 BEFORE the YAML -> CSV refactor; ``tests/test_prompt_snapshot.py``
recomputes them with the current code and asserts equality.

Only behaviour is compared: rendered messages, trial ids, record ids, seeds,
execution order and call counts. Template version strings, file hashes and the
default run id are expected to change with a refactor and are not compared.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "prompt_snapshot.jsonl"
TEXTS_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "prompt_snapshot_texts.jsonl"
SNAPSHOT_RUN_ID = "snapshot_run"     # fixed run id for record ids of runs whose default run id is a hash
SAMPLE_EVERY = 211                   # pilot/main: one trial row per SAMPLE_EVERY trials (plus group firsts)


def _h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _digest(lines) -> str:
    h = hashlib.sha256()
    for line in lines:
        h.update(line.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def _trial_key(t) -> str:
    return "|".join(str(x) for x in (
        t.trial_id, t.task_type, t.prompt_condition, t.template_id, t.model_alias, t.repetitions, t.occupation,
        t.prompt_variant, t.arm, t.temperature, ",".join(t.stimulus_ids), ",".join(t.base_cv_ids),
        ",".join(t.nationalities), t.clone_type, t.qualification_tier, t.fc_order, t.quad_id, t.item_id,
        t.context, t.base_country))


def _group(t) -> str:
    return f"{t.model_alias}|{t.arm}|{t.prompt_condition}|{t.prompt_variant}|{t.clone_type}|{t.context}"


def compute_run_snapshot(run: str, exp, *, all_trial_rows: bool, record_run_id: str | None = None):
    """Rows (dicts) describing one experiment. ``record_run_id`` defaults to the
    experiment's own run id; pass SNAPSHOT_RUN_ID for runs with a hashed default id."""
    from hiringaudit.prompts import prompt_sha256
    from hiringaudit.randomization import expand_calls
    from hiringaudit.runner import PromptBuilder, make_plan

    rid = record_run_id or exp.run_id
    trials = exp.plan.trials
    builder = PromptBuilder(exp)
    calls = expand_calls(trials, rid, exp.cfg.seed, exp.cfg.models)
    prompt_lines, rows, texts, seen_groups = [], [], [], set()
    for i, t in enumerate(trials):
        msgs = builder.messages(t)
        ph = prompt_sha256(msgs)
        prompt_lines.append(f"{t.trial_id}|{ph}")
        g = _group(t)
        first = g not in seen_groups
        seen_groups.add(g)
        if all_trial_rows or first or i % SAMPLE_EVERY == 0:
            rows.append({"kind": "trial", "run": run, "trial_id": t.trial_id, "prompt": ph[:16]})
        if first and (run == "mock" or t.prompt_condition == "principle_probe"):
            texts.append({"kind": "prompt_text", "run": run, "trial_id": t.trial_id, "group": g,
                          "system": msgs[0]["content"], "user": msgs[1]["content"]})
    plan = make_plan(exp)
    summary = {
        "kind": "summary", "run": run, "experiment_id": exp.cfg.experiment_id,
        "record_run_id": rid, "config_hash": exp.cfg.config_hash(),
        "n_trials": len(trials), "n_calls": len(calls),
        "calls_by_model_group": {f"{m}|{g}": n for (m, g), n in sorted(plan.calls.items())},
        "trials_digest": _digest(_trial_key(t) for t in trials),
        "calls_digest": _digest(f"{c.record_id}|{c.trial.trial_id}|{c.repetition}|{c.seed}|{c.execution_index}"
                                for c in calls),
        "prompts_digest": _digest(prompt_lines),
        "fc_quads_digest": _digest(json.dumps(q.__dict__, sort_keys=True) for q in exp.plan.fc_design),
    }
    return [summary, *rows], texts


def compute_stimulus_snapshot(jobs, base_countries, cvs, nationalities, cv_template):
    """One row per localized job ad (occupation x base country) and one per base CV
    (digest over all its clones, including the positive control)."""
    from hiringaudit.prompts import render_job_ad
    from hiringaudit.stimuli.render import COUNTERFACTUAL, POSITIVE_CONTROL, render_clone

    rows, texts = [], []
    for occ, job in jobs.items():
        for code, base in sorted(base_countries.items()):
            ad = render_job_ad(job.localize(base.base_city, base.name))
            rows.append({"kind": "job_ad", "occupation": occ, "base_country": code, "sha256": _h(ad)})
            if code == "ARE":
                texts.append({"kind": "job_ad_text", "occupation": occ, "base_country": code, "text": ad})
    for cv in cvs:
        clones = [render_clone(cv, n.demonym, COUNTERFACTUAL, cv_template) for n in nationalities.conditions]
        clones.append(render_clone(cv, None, POSITIVE_CONTROL, cv_template))
        rows.append({"kind": "cv", "cv_id": cv["cv_id"], "n_clones": len(clones), "digest": _digest(clones)})
        if cv["cv_id"] in ("swdev_01", "whse_03"):
            texts.append({"kind": "cv_text", "cv_id": cv["cv_id"], "deu": clones[nationalities.codes.index("DEU")],
                          "positive_control": clones[-1]})
    return rows, texts


def _alternation_tokens(pat) -> list[str]:
    if pat is None:
        return []
    s = pat.pattern
    inner = s[len(r"(?<![\w])("):-len(r")(?![\w])")]
    return sorted(inner.split("|"))


def structure_rows(*, jobs, models, principle, text_flag_patterns, leak_rules, pools, confirmatory, configs):
    """Digests of what each config file loads into (in-memory structures, not file bytes)."""
    from dataclasses import asdict

    from hiringaudit.utils import stable_hash

    lr = leak_rules
    out = {
        "jobs": stable_hash([[occ, j.model_dump(mode="json")] for occ, j in jobs.items()]),
        "models": stable_hash([[a, s.model_dump(mode="json")] for a, s in models.items()]),
        "principle": stable_hash({"generic": principle.generic_context, "occupation": principle.occupation_context,
                                  "items": [i.model_dump(mode="json") for i in principle.items]}),
        "text_flags": stable_hash({f: p.pattern for f, p in text_flag_patterns.items()}),
        "leak_case_sensitive": stable_hash(_alternation_tokens(lr.case_sensitive)),
        "leak_case_insensitive": stable_hash(_alternation_tokens(lr.case_insensitive)),
        "leak_texts_only": stable_hash(_alternation_tokens(lr.texts_only)),
        "leak_forbidden_characters": stable_hash(sorted(lr.forbidden_characters)),
        "leak_cv_allowed": stable_hash(sorted(lr.cv_allowed)),
        "base_countries": stable_hash({c: asdict(b) for c, b in lr.base_countries.items()}),
        "cv_pools": stable_hash(pools),
        "analysis_confirmatory": stable_hash(confirmatory),
    }
    for run, cfg in configs.items():
        out[f"config_dump:{run}"] = stable_hash(cfg.model_dump(mode="json"))
    return [{"kind": "structure", "name": k, "digest": v} for k, v in out.items()]


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def counts(rows) -> Counter:
    return Counter(r["kind"] for r in rows)
