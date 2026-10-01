"""Behaviour is unchanged by the YAML -> CSV refactor (2026-10-01).

``tests/fixtures/prompt_snapshot.jsonl`` was captured with the pre-refactor code
(YAML configs, prompts/*.txt). This test recomputes it from the CSV inputs and
asserts that every rendered prompt (system + user message of every trial of the
mock, pilot and main runs), every localized job ad, every CV clone, every trial
id, record id, seed, execution index and call count, and what every config table
loads into, are identical.

Record ids depend on the run id. The mock run has a fixed run id; for pilot and
main (whose default run id is a hash of the input files, which the refactor
changed) record ids are compared under the fixed run id ``snapshot_lib.SNAPSHOT_RUN_ID``.
"""

from __future__ import annotations

import pytest
import snapshot_lib as S
from eng_helpers import REPO, make_paths

from hiringaudit.analysis.settings import load_confirmatory
from hiringaudit.config import (load_jobs, load_models, load_nationalities, load_principle_items, load_run_config,
                                load_text_flags)
from hiringaudit.leaks import LeakRules
from hiringaudit.parse_outputs import compile_text_flags
from hiringaudit.runner import load_experiment
from hiringaudit.stimuli.building_blocks import load_building_blocks
from hiringaudit.stimuli.render import load_template
from hiringaudit.stimuli.setting import load_base_countries
from hiringaudit.tables import load_cv_table

FIXTURE = S.read_jsonl(S.FIXTURE)
RUNS = ("mock", "pilot", "main")


def _expected(kind: str, **match) -> list[dict]:
    return [r for r in FIXTURE if r["kind"] == kind and all(r.get(k) == v for k, v in match.items())]


@pytest.fixture(scope="module")
def paths(tmp_path_factory):
    return make_paths(tmp_path_factory.mktemp("snapshot"))


@pytest.mark.parametrize("run", RUNS)
def test_every_prompt_trial_and_call_is_unchanged(paths, run):
    exp = load_experiment(run, paths)
    assert exp.stimulus_problems == []
    if run == "mock":
        assert exp.run_id == "mock_pipeline_test"
    rows, _ = S.compute_run_snapshot(run, exp, all_trial_rows=(run == "mock"),
                                     record_run_id=None if run == "mock" else S.SNAPSHOT_RUN_ID)
    summary, trials = rows[0], rows[1:]
    expected = _expected("summary", run=run)[0]
    want = {r["trial_id"]: r["prompt"] for r in _expected("trial", run=run)}
    got = {r["trial_id"]: r["prompt"] for r in trials}
    changed = sorted(t for t in want if got.get(t) != want[t])
    assert not changed, f"{len(changed)} trial(s) render differently, e.g. {changed[:5]}"
    for key in ("n_trials", "n_calls", "calls_by_model_group", "trials_digest", "calls_digest", "prompts_digest",
                "fc_quads_digest", "config_hash", "experiment_id", "record_run_id"):
        assert summary[key] == expected[key], key


def test_plan_call_counts():
    totals = {r["run"]: r["n_calls"] for r in _expected("summary")}
    assert totals["pilot"] == 43228 and totals["main"] == 106548


def test_job_ads_and_cv_clones_are_unchanged(paths):
    nats = load_nationalities(paths.nationalities_file)
    bases = load_base_countries(paths.base_countries_file, paths.institutions_file)
    rows, _ = S.compute_stimulus_snapshot(load_jobs(paths.jobs_file), bases, load_cv_table(paths.cv_table_file),
                                          nats, load_template(paths.cv_template_file))
    assert [r for r in rows if r["kind"] == "job_ad"] == _expected("job_ad")
    assert [r for r in rows if r["kind"] == "cv"] == _expected("cv")


def test_config_tables_load_into_the_same_structures(paths):
    nats = load_nationalities(paths.nationalities_file)
    bases = load_base_countries(paths.base_countries_file, paths.institutions_file)
    rows = S.structure_rows(
        jobs=load_jobs(paths.jobs_file), models=load_models(paths.models_file),
        principle=load_principle_items(paths.principle_items_file, paths.prompt_parts_file),
        text_flag_patterns=compile_text_flags(load_text_flags(paths.text_flags_file), nats),
        leak_rules=LeakRules.load(paths.leak_terms_file, nats, bases),
        pools=load_building_blocks(paths.building_blocks_dir),
        confirmatory=load_confirmatory(REPO / "config" / "analysis_settings.csv"),
        configs={r: load_run_config(paths.runs_file, r) for r in RUNS})
    got = {r["name"]: r["digest"] for r in rows}
    want = {r["name"]: r["digest"] for r in _expected("structure")}
    assert sorted(k for k in want if got.get(k) != want[k]) == []
