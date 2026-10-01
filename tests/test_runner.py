"""Runner: logging completeness, resume/idempotency, retries, guards, stop rule, parsing to tables."""

from __future__ import annotations

import json
import shutil
from collections import Counter

import pandas as pd
import pytest
from eng_helpers import (REPO, copy_config, copy_stimuli, edit_cv_row, make_root_copy, read_table,  # noqa: F401
                         stim_paths, tiny_config, write_table)

import hiringaudit.runner as runner_mod
from hiringaudit.cli import main
from hiringaudit.config import load_nationalities, load_text_flags
from hiringaudit.parse_outputs import EXPLORATORY_SUFFIX, DuplicateRecordError, ParserMismatch, parse_outputs
from hiringaudit.paths import ProjectPaths
from hiringaudit.providers import ChatResponse, NonRetryableProviderError, Provider, RetryableProviderError
from hiringaudit.providers.mock import MockProvider
from hiringaudit.runner import (RealCallsNotAllowed, RunConfigMismatch, RunIdPolicyError, RunOptions, coverage,
                                load_experiment, run_experiment)
from hiringaudit.schemas import EVALUATION_COLUMNS, FORCED_CHOICE_COLUMNS, PRINCIPLE_COLUMNS, RAW_RECORD_FIELDS
from hiringaudit.utils import iter_jsonl, sha256_file

NATS = load_nationalities(REPO / "stimuli" / "nationalities.csv")
CODING_PATH = REPO / "config" / "text_flags.csv"
CODING = load_text_flags(CODING_PATH)
QUIET = dict(show_progress=False)


def _paths(stim_paths, tmp_path):  # noqa: F811
    return stim_paths.with_overrides(data_dir=tmp_path / "data")


def _records(exp):
    return [o for _, o, _ in iter_jsonl(exp.paths.raw_run_dir(exp.run_id) / "responses.jsonl") if o]


def _parse(exp, **kw):
    return parse_outputs(exp.paths.raw_run_dir(exp.run_id), exp.paths.processed_run_dir(exp.run_id), NATS, CODING,
                         text_flags_path=CODING_PATH, **kw)


def test_mock_run_complete_and_logged(stim_paths, tmp_path):  # noqa: F811
    exp = load_experiment(tiny_config(), _paths(stim_paths, tmp_path))
    summary = run_experiment(exp, RunOptions(**QUIET))
    cov = coverage(exp)
    assert cov["missing"] == 0 and cov["duplicates"] == 0 and cov["unexpected"] == 0
    assert summary.written == cov["planned"]
    recs = _records(exp)
    for r in recs:
        missing = [f for f in RAW_RECORD_FIELDS if f not in r]
        assert not missing, missing
        assert r["is_mock"] is True and r["model_revision"] == "hiringaudit-mock-v2"
    statuses = Counter(r["parse_status"] for r in recs)
    assert {"ok", "malformed_json", "schema_violation", "refusal", "empty", "api_error"} <= set(statuses)
    raw = exp.paths.raw_run_dir(exp.run_id)
    prompts = [o["prompt_sha256"] for _, o, _ in iter_jsonl(raw / "prompts.jsonl") if o]
    assert len(prompts) == len(set(prompts)) and {r["prompt_sha256"] for r in recs} == set(prompts)
    man = json.loads((raw / "run_manifest.json").read_text(encoding="utf-8"))
    for key in ("identity", "config_snapshot", "prompt_templates", "seeds", "model_provenance",
                "parser_version", "parser_fingerprint", "input_file_sha256", "sessions"):
        assert key in man
    assert set(man["identity"]["input_files"]) == {"cvs.csv", "nationalities.csv", "cv_template.txt", "jobs.csv",
                                                   "principle_items.csv", "prompt_parts.csv", "prompt_recipes.csv"}
    assert man["config_source"] == "<dict>" and "system" in man["identity"]["prompt_templates"]
    # every record names its stimulus; every rendered prompt is stored once in prompts.jsonl
    assert all(r["stimulus_ids"] for r in recs if r["task_type"] != "principle_probe")
    s = man["sessions"][-1]
    assert s["status"] == "completed" and s["environment"]["python"] and "git" in s["environment"]
    assert (raw / "fc_design.json").exists()
    assert sorted(r["execution_index"] for r in recs) == list(range(len(recs)))


def test_resume_after_interrupt_no_duplicates(stim_paths, tmp_path, monkeypatch):  # noqa: F811
    exp = load_experiment(tiny_config(), _paths(stim_paths, tmp_path))
    real_complete = MockProvider.complete
    n = {"calls": 0}

    def flaky(self, req):
        n["calls"] += 1
        if n["calls"] == 60:
            raise KeyboardInterrupt
        return real_complete(self, req)

    monkeypatch.setattr(MockProvider, "complete", flaky)
    with pytest.raises(KeyboardInterrupt):
        run_experiment(exp, RunOptions(**QUIET))
    path = exp.paths.raw_run_dir(exp.run_id) / "responses.jsonl"
    first = path.read_bytes()
    first_recs = _records(exp)
    assert 0 < len(first_recs) < coverage(exp)["planned"]
    man = json.loads((exp.paths.raw_run_dir(exp.run_id) / "run_manifest.json").read_text(encoding="utf-8"))
    assert man["sessions"][-1]["status"] == "interrupted"

    monkeypatch.setattr(MockProvider, "complete", real_complete)
    s2 = run_experiment(exp, RunOptions(**QUIET))
    assert s2.already_recorded == sum(r["parse_status"] != "api_error" for r in first_recs)
    assert path.read_bytes().startswith(first), "raw records are never rewritten"
    cov = coverage(exp)
    assert cov["missing"] == 0 and cov["duplicates"] == 0
    s3 = run_experiment(exp, RunOptions(**QUIET))
    assert s3.written == cov["api_error_only"]  # only api_error-only calls are attempted again (M7)
    assert coverage(exp)["duplicates"] == 0


def test_corrupt_trailing_line_is_reported_not_dropped(stim_paths, tmp_path):  # noqa: F811
    exp = load_experiment(tiny_config(), _paths(stim_paths, tmp_path))
    run_experiment(exp, RunOptions(limit=10, **QUIET))
    raw = exp.paths.raw_run_dir(exp.run_id)
    with open(raw / "responses.jsonl", "a", encoding="utf-8") as fh:
        fh.write('{"record_id": "r_trunc')  # simulated crash mid-write
    run_experiment(exp, RunOptions(**QUIET))
    cov = coverage(exp)
    assert cov["missing"] == 0 and cov["duplicates"] == 0
    assert len(_parse(exp)["corrupt_raw_lines"]) == 1


# ---- resume identity (H3) ----
def test_config_change_refuses_to_mix(stim_paths, tmp_path):  # noqa: F811
    p = _paths(stim_paths, tmp_path)
    run_experiment(load_experiment(tiny_config(run_id="mock_fixed"), p), RunOptions(limit=5, **QUIET))
    with pytest.raises(RunConfigMismatch):
        run_experiment(load_experiment(tiny_config(run_id="mock_fixed", seed=1), p), RunOptions(**QUIET))


def _replace_in(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new), encoding="utf-8")


@pytest.mark.parametrize("edit,which", [
    (lambda p: _replace_in(p.jobs_file, "Our team of 70 people", "Our team of 75 people"), "jobs.csv"),
    (lambda p: _replace_in(p.models_file, "hiringaudit-mock-v2", "hiringaudit-mock-v3"), "models"),
    (lambda p: _replace_in(p.prompt_parts_file, "Please review the application below",
                           "Please assess the application below"), "prompt_templates"),
    (lambda p: _replace_in(p.prompt_parts_file, "screened in general.", "screened in general today."),
     "prompt_parts.csv"),
])
def test_changed_inputs_refuse_resume(stim_paths, tmp_path, edit, which):  # noqa: F811
    p = copy_config(tmp_path, copy_stimuli(tmp_path, _paths(stim_paths, tmp_path)))
    prompts = tmp_path / "prompts_copy"
    shutil.copytree(REPO / "prompts", prompts)
    p = p.with_overrides(prompts_dir=prompts)
    run_experiment(load_experiment(tiny_config(run_id="mock_same"), p), RunOptions(limit=5, **QUIET))
    edit(p)
    with pytest.raises(RunConfigMismatch, match=which):
        run_experiment(load_experiment(tiny_config(run_id="mock_same"), p), RunOptions(**QUIET))
    # the default run id changes with the inputs, so nothing is mixed silently
    assert load_experiment(tiny_config(), p).run_id != load_experiment(tiny_config(), _paths(stim_paths, tmp_path)).run_id


def test_changed_cv_table_refuses_resume(stim_paths, tmp_path):  # noqa: F811
    p = copy_stimuli(tmp_path, _paths(stim_paths, tmp_path))
    run_experiment(load_experiment(tiny_config(run_id="mock_same"), p), RunOptions(limit=5, **QUIET))
    edit_cv_row(p, "swdev_01", profile="Backend developer with a slightly edited profile.")
    with pytest.raises(RunConfigMismatch, match="cvs.csv"):
        run_experiment(load_experiment(tiny_config(run_id="mock_same"), p), RunOptions(**QUIET))


# ---- real-call guards (H3, L5) ----
def test_real_provider_refused_without_flag(stim_paths, tmp_path):  # noqa: F811
    exp = load_experiment(tiny_config(experiment_id="unit_real", models=["qwen3-8b"]), _paths(stim_paths, tmp_path))
    with pytest.raises(RealCallsNotAllowed):
        run_experiment(exp, RunOptions(**QUIET))
    assert not exp.paths.raw_run_dir(exp.run_id).exists(), "nothing is written before the refusal"


def test_real_calls_refused_when_unpinned(stim_paths, tmp_path):  # noqa: F811
    exp = load_experiment(tiny_config(experiment_id="unit_real", models=["qwen3-8b"]), _paths(stim_paths, tmp_path))
    with pytest.raises(RealCallsNotAllowed, match="revision"):
        run_experiment(exp, RunOptions(allow_real_calls=True, **QUIET))
    assert not exp.paths.raw_run_dir(exp.run_id).exists()


def _pinned_paths(stim_paths, tmp_path):  # noqa: F811
    p = copy_config(tmp_path, _paths(stim_paths, tmp_path))
    cols, rows = read_table(p.models_file)
    for r in rows:
        if r["alias"] == "qwen3-8b":
            r["revision"] = "0123456789abcdef"
    write_table(p.models_file, cols, rows)
    return p


@pytest.mark.parametrize("dirty,match", [(["src/hiringaudit/x.py"], "modified or untracked"),
                                         (None, "cannot verify the git state")])
def test_real_calls_refused_on_uncommitted_tree(stim_paths, tmp_path, monkeypatch, dirty, match):  # noqa: F811
    monkeypatch.setattr(runner_mod, "uncommitted_paths", lambda root: dirty)
    exp = load_experiment(tiny_config(experiment_id="unit_real", models=["qwen3-8b"]), _pinned_paths(stim_paths, tmp_path))
    with pytest.raises(RealCallsNotAllowed, match=match):
        run_experiment(exp, RunOptions(allow_real_calls=True, **QUIET))


class FakeVLLM(Provider):
    name = "openai_compatible"

    def complete(self, request):  # pragma: no cover - must never be reached
        raise AssertionError("no call may be made")

    def introspect(self):
        return {"endpoint": "http://fake/v1", "served_models": [{"id": "some/other-model"}], "server_version": "x"}


def test_real_calls_refused_when_model_not_served(stim_paths, tmp_path, monkeypatch):  # noqa: F811
    monkeypatch.setattr(runner_mod, "uncommitted_paths", lambda root: [])
    exp = load_experiment(tiny_config(experiment_id="unit_real", models=["qwen3-8b"]), _pinned_paths(stim_paths, tmp_path))
    with pytest.raises(RealCallsNotAllowed, match="serves"):
        run_experiment(exp, RunOptions(allow_real_calls=True, **QUIET), provider_factory=FakeVLLM)


def test_run_id_policy(stim_paths, tmp_path, monkeypatch):  # noqa: F811
    p = _paths(stim_paths, tmp_path)
    with pytest.raises(RunIdPolicyError):
        run_experiment(load_experiment(tiny_config(run_id="real_looking"), p), RunOptions(**QUIET))
    monkeypatch.setattr(runner_mod, "uncommitted_paths", lambda root: [])
    real = load_experiment(tiny_config(experiment_id="unit_real", models=["qwen3-8b"], run_id="mock_disguised"),
                           _pinned_paths(stim_paths, tmp_path))
    with pytest.raises(RunIdPolicyError):
        run_experiment(real, RunOptions(allow_real_calls=True, **QUIET))


def test_cli_refuses_real_provider(tmp_path, capsys):
    root = make_root_copy(tmp_path)
    assert main(["--root", str(root), "run", "--run", "pilot", "--quiet"]) == 2
    assert "without --allow-real-calls" in capsys.readouterr().err
    assert main(["--root", str(root), "run", "--run", "pilot", "--quiet", "--allow-real-calls"]) == 2  # unpinned
    assert "revision" in capsys.readouterr().err


def test_cli_rejects_the_removed_config_flag_and_unknown_runs(tmp_path, capsys):
    root = make_root_copy(tmp_path)
    assert main(["--root", str(root), "plan", "--config", "config/pilot.yaml"]) == 2
    assert "--config was removed" in capsys.readouterr().err
    assert main(["--root", str(root), "plan", "--run", "config/pilot.yaml"]) == 2
    assert "not a run name" in capsys.readouterr().err
    assert main(["--root", str(root), "plan", "--run", "pilot2"]) == 2
    assert "unknown run 'pilot2'" in capsys.readouterr().err
    assert main(["--root", str(root), "plan", "--run", "pilot"]) == 0
    assert "43228" in capsys.readouterr().out


def test_runs_table_states_every_setting(tmp_path):
    from hiringaudit.config import RunConfigError, load_run_config

    p = copy_config(tmp_path, ProjectPaths.from_root(REPO))
    cols, rows = read_table(p.runs_file)
    rows[1]["max_tokens"] = ""
    write_table(p.runs_file, cols, rows)
    with pytest.raises(Exception, match="max_tokens"):
        load_run_config(p.runs_file, rows[1]["run"])
    with pytest.raises(RunConfigError, match="unknown run"):
        load_run_config(REPO / "config" / "runs.csv", "nope")


# ---- retries (A4, M7) ----
class ScriptedProvider(Provider):
    """Replays a script of outcomes: exceptions are raised, strings are returned."""

    name = "scripted"

    def __init__(self, spec, script):
        super().__init__(spec)
        self.script = list(script)

    def complete(self, request):
        item = self.script.pop(0) if self.script else '{"overall_fit": 50, "interview": "no", "confidence": 50, "reason": "x"}'
        if isinstance(item, Exception):
            raise item
        return ChatResponse(text=item, finish_reason="stop", usage=None, latency_ms=1.0)


def _one_call_config(**kw):
    return tiny_config(nationalities=["DEU", "EGY"], prompt_variants=["k1"],
                       base_cvs={"software_developer": ["swdev_01"]},
                       conditions={"baseline": {"enabled": True, "repetitions": 1},
                                   "neutrality": {"enabled": False}, "forced_choice": {"enabled": False},
                                   "forced_choice_neutrality": {"enabled": False},
                                   "principle_probe": {"enabled": False}},
                       positive_control=False, **kw)


@pytest.mark.parametrize("script,status,attempts", [
    ([RetryableProviderError("503"), RetryableProviderError("timeout")], "ok", 3),
    ([RetryableProviderError("503")] * 3, "api_error", 3),
    ([NonRetryableProviderError("400")], "api_error", 1),
    (["{not json"], "malformed_json", 1),        # A4: bad outputs are terminal, never re-sampled
    (["I'm sorry, I can't help with that."], "refusal", 1),
    ([""], "empty", 1),
])
def test_retry_policy(stim_paths, tmp_path, script, status, attempts):  # noqa: F811
    exp = load_experiment(_one_call_config(), _paths(stim_paths, tmp_path))
    run_experiment(exp, RunOptions(workers=1, **QUIET), provider_factory=lambda spec: ScriptedProvider(spec, script))
    first = sorted(_records(exp), key=lambda r: r["execution_index"])[0]
    assert first["parse_status"] == status and first["attempts"] == attempts
    assert first["transport_retries"] == attempts - 1
    assert len(first["attempt_errors"]) == (attempts if status == "api_error" else attempts - 1)


def test_api_error_calls_are_redone_on_resume(stim_paths, tmp_path):  # noqa: F811  (M7)
    exp = load_experiment(_one_call_config(), _paths(stim_paths, tmp_path))
    run_experiment(exp, RunOptions(workers=1, **QUIET),
                   provider_factory=lambda spec: ScriptedProvider(spec, [NonRetryableProviderError("400")]))
    failed = [r for r in _records(exp) if r["parse_status"] == "api_error"]
    assert len(failed) == 1
    s2 = run_experiment(exp, RunOptions(workers=1, **QUIET), provider_factory=lambda spec: ScriptedProvider(spec, []))
    assert s2.written == 1
    redo = [r for r in _records(exp) if r["record_id"] == failed[0]["record_id"]]
    assert [r["parse_status"] for r in redo] == ["api_error", "ok"]
    assert redo[1]["attempts"] == 2 and redo[1]["prior_attempts"] == 1
    summary = _parse(exp)
    assert summary["n_superseded_api_error_records"] == 1 and summary["parse_status_counts"] == {"ok": 2}
    assert run_experiment(exp, RunOptions(**QUIET), provider_factory=lambda s: ScriptedProvider(s, [])).written == 0


# ---- technical stop rule (M8) ----
def test_stop_rule_stops_a_failing_model(stim_paths, tmp_path):  # noqa: F811
    cfg = tiny_config(stop_rule={"enabled": True, "first_fraction": 0.05, "max_non_ok_share": 0.10},
                      mock={"rates": {"malformed_json": 0.5}})
    exp = load_experiment(cfg, _paths(stim_paths, tmp_path))
    s = run_experiment(exp, RunOptions(**QUIET))
    assert "mock" in s.stopped_models and s.written < coverage(exp)["planned"]
    man = json.loads((exp.paths.raw_run_dir(exp.run_id) / "run_manifest.json").read_text(encoding="utf-8"))
    verdict = man["stop_rule"]["models"]["mock"]
    assert verdict["stopped"] and verdict["non_ok_share"] > 0.10
    assert run_experiment(exp, RunOptions(**QUIET)).written == 0  # stays stopped in this run


def test_stop_rule_passes_a_healthy_model(stim_paths, tmp_path):  # noqa: F811
    cfg = tiny_config(stop_rule={"enabled": True}, mock={"rates": {}})
    exp = load_experiment(cfg, _paths(stim_paths, tmp_path))
    s = run_experiment(exp, RunOptions(**QUIET))
    assert not s.stopped_models and s.written == coverage(exp)["planned"]
    man = json.loads((exp.paths.raw_run_dir(exp.run_id) / "run_manifest.json").read_text(encoding="utf-8"))
    assert man["stop_rule"]["models"]["mock"]["stopped"] is False


# ---- parsing to tables ----
def test_parse_tables_match_schema_and_leave_raw_untouched(stim_paths, tmp_path):  # noqa: F811
    exp = load_experiment(tiny_config(), _paths(stim_paths, tmp_path))
    run_experiment(exp, RunOptions(**QUIET))
    raw = exp.paths.raw_run_dir(exp.run_id)
    before = sha256_file(raw / "responses.jsonl")
    _parse(exp)
    _parse(exp)  # re-runnable
    assert sha256_file(raw / "responses.jsonl") == before
    out = exp.paths.processed_run_dir(exp.run_id)
    ev = pd.read_csv(out / "evaluations.csv")  # pandas defaults: "NONE" must survive
    fc = pd.read_csv(out / "forced_choice.csv")
    pr = pd.read_csv(out / "principle.csv")
    assert tuple(ev.columns) == EVALUATION_COLUMNS
    assert tuple(fc.columns) == FORCED_CHOICE_COLUMNS
    assert tuple(pr.columns) == PRINCIPLE_COLUMNS
    for df in (ev, fc, pr):
        assert df["is_mock"].all() and df["prompt_sha256"].notna().all() and df["user_prompt_version"].notna().all()
    assert "NONE" in set(ev["nationality"])
    ok = ev[ev.parse_status == "ok"]
    assert ok["overall_fit"].notna().all() and set(ok["interview"].unique()) <= {0, 1}
    assert ev[ev.parse_status != "ok"]["overall_fit"].isna().all()
    assert set(ev["clone_type"]) == {"counterfactual", "positive_control"}
    assert set(ev["prompt_variant"]) == {"k1", "k2"}
    assert set(ev["pronoun_gender"].dropna()) <= {"he", "she", "they", "none"}
    plc = ev[ev.nationality_group == "placebo"]
    assert set(plc["nationality"]) == {"URY", "MWI"}
    assert set(plc["prompt_condition"]) == {"baseline"} and set(plc["arm"]) == {"primary"}
    assert set(plc["clone_type"]) == {"counterfactual"}
    okfc = fc[fc.parse_status == "ok"]
    assert (okfc.apply(lambda r: r.chosen_nationality == (r.nationality_a if r.choice == "A" else r.nationality_b),
                       axis=1)).all()
    assert not ({"NONE", "URY", "MWI"} & (set(fc["nationality_a"]) | set(fc["nationality_b"])))
    okpr = pr[pr.parse_status == "ok"]
    assert okpr[okpr.keying == "control"]["endorses_neutrality"].isna().all()
    rev = okpr[okpr.keying == "reverse"]
    assert (rev["endorses_neutrality"] != rev["answer"]).all()
    pro = okpr[okpr.keying == "pro"]
    assert (pro["endorses_neutrality"] == pro["answer"]).all()


def test_parser_change_requires_exploratory(stim_paths, tmp_path):  # noqa: F811  (M11)
    exp = load_experiment(tiny_config(), _paths(stim_paths, tmp_path))
    run_experiment(exp, RunOptions(limit=20, **QUIET))
    man_path = exp.paths.raw_run_dir(exp.run_id) / "run_manifest.json"
    man = json.loads(man_path.read_text(encoding="utf-8"))
    man["parser_fingerprint"] = "0" * 64
    man_path.write_text(json.dumps(man), encoding="utf-8")
    with pytest.raises(ParserMismatch):
        _parse(exp)
    summary = _parse(exp, exploratory=True)
    out = exp.paths.processed_run_dir(exp.run_id).with_name(exp.run_id + EXPLORATORY_SUFFIX)
    assert summary["parse_mode"] == "exploratory" and "EXPLORATORY" in summary["WARNING"]
    assert (out / "EXPLORATORY_PARSE.txt").exists() and (out / "evaluations.csv").exists()
    assert not exp.paths.processed_run_dir(exp.run_id).exists()


def test_two_terminal_records_for_one_id_are_rejected(stim_paths, tmp_path):  # noqa: F811
    exp = load_experiment(tiny_config(mock={"rates": {}}), _paths(stim_paths, tmp_path))
    run_experiment(exp, RunOptions(limit=3, **QUIET))
    raw = exp.paths.raw_run_dir(exp.run_id)
    line = (raw / "responses.jsonl").read_text(encoding="utf-8").splitlines()[0]
    with open(raw / "responses.jsonl", "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    with pytest.raises(DuplicateRecordError):
        _parse(exp)


def test_threaded_run_is_complete(stim_paths, tmp_path):  # noqa: F811
    exp = load_experiment(tiny_config(), _paths(stim_paths, tmp_path))
    run_experiment(exp, RunOptions(workers=4, **QUIET))
    cov = coverage(exp)
    assert cov["missing"] == 0 and cov["duplicates"] == 0


def test_plan_counts_match_planned_calls(stim_paths, tmp_path):  # noqa: F811
    from hiringaudit.runner import make_plan

    exp = load_experiment(tiny_config(), _paths(stim_paths, tmp_path))
    plan = make_plan(exp)
    assert plan.total_calls == coverage(exp)["planned"]
    text = plan.format()
    for g in ("ROUGH", "baseline[positive_control]", "baseline[placebo]", "principle_probe"):
        assert g in text


# ---- round-2 review items ----
def test_real_calls_refused_when_code_repo_is_dirty(stim_paths, tmp_path, monkeypatch):  # noqa: F811  (N2)
    from pathlib import Path

    from hiringaudit.manifest import package_root

    def fake(root):
        return ["src/hiringaudit/runner.py"] if Path(root).resolve() == package_root() else []

    monkeypatch.setattr(runner_mod, "uncommitted_paths", fake)
    data_root = tmp_path / "clean_data_root"  # a clean data root elsewhere; the code repo is dirty
    data_root.mkdir()
    paths = _pinned_paths(stim_paths, tmp_path).with_overrides(root=data_root)
    exp = load_experiment(tiny_config(experiment_id="unit_real", models=["qwen3-8b"]), paths)
    with pytest.raises(RealCallsNotAllowed, match=r"code \(hiringaudit package\)"):
        run_experiment(exp, RunOptions(allow_real_calls=True, **QUIET))


def test_stop_rule_ignores_transport_errors(stim_paths, tmp_path):  # noqa: F811  (N6)
    cfg = tiny_config(stop_rule={"enabled": True, "first_fraction": 0.05, "max_non_ok_share": 0.10},
                      mock={"rates": {"api_error_fatal": 0.5}})
    exp = load_experiment(cfg, _paths(stim_paths, tmp_path))
    s = run_experiment(exp, RunOptions(**QUIET))
    assert not s.stopped_models
    verdict = json.loads((exp.paths.raw_run_dir(exp.run_id) / "run_manifest.json").read_text(encoding="utf-8"))[
        "stop_rule"]["models"]["mock"]
    assert verdict["stopped"] is False and verdict["non_ok"] == 0


def test_api_error_reattempts_are_capped(stim_paths, tmp_path):  # noqa: F811  (N7)
    exp = load_experiment(_one_call_config(), _paths(stim_paths, tmp_path))
    fail = lambda spec: ScriptedProvider(spec, [NonRetryableProviderError("400")] * 2)  # noqa: E731
    written = [run_experiment(exp, RunOptions(workers=1, **QUIET), provider_factory=fail).written for _ in range(4)]
    assert written == [2, 2, 2, 0]
    man = json.loads((exp.paths.raw_run_dir(exp.run_id) / "run_manifest.json").read_text(encoding="utf-8"))
    assert len(man["sessions"][-1]["api_error_terminal"]) == 2
    assert _parse(exp)["parse_status_counts"] == {"api_error": 2}


def test_host_national_in_raw_records_and_tables(stim_paths, tmp_path):  # noqa: F811
    """host_national = (nationality code == the CV's base country); swdev_01/04 are set
    in ARE, swdev_02/05 in SAU (user request 2026-10-01)."""
    cfg = tiny_config(nationalities=["DEU", "EGY", "ARE", "SAU", "POL", "NONE", "URY"],
                      mock={"rates": {}}, stop_rule={"enabled": False})
    exp = load_experiment(cfg, _paths(stim_paths, tmp_path))
    run_experiment(exp, RunOptions(**QUIET))
    base = {cv_id: cv["base_country"] for cv_id, cv in exp.cvs.items()}
    assert {base[c] for c in ("swdev_01", "swdev_04")} == {"ARE"} and {base[c] for c in ("swdev_02", "swdev_05")} == {"SAU"}
    for r in _records(exp):
        if r["task_type"] == "principle_probe":
            assert r["base_country"] is None and r["host_national"] is None
            continue
        assert {base[c] for c in r["base_cv_ids"]} == {r["base_country"]}
        assert r["host_national"] == [n == r["base_country"] for n in r["nationalities"]]
    _parse(exp)
    out = exp.paths.processed_run_dir(exp.run_id)
    ev = pd.read_csv(out / "evaluations.csv", keep_default_na=False, na_values=[""])
    fc = pd.read_csv(out / "forced_choice.csv", keep_default_na=False, na_values=[""])
    assert (ev["base_country"] == ev["base_cv_id"].map(base)).all()
    assert (ev["host_national"] == (ev["nationality"] == ev["base_country"])).all()
    assert ev["host_national"].any() and not ev.loc[ev["nationality_group"] != "arab", "host_national"].any()
    assert set(ev.loc[ev["host_national"], "nationality"]) == {"ARE", "SAU"}
    assert (fc["base_country"] == fc["cv_a"].map(base)).all() and (fc["base_country"] == fc["cv_b"].map(base)).all()
    assert (fc["host_national_a"] == (fc["nationality_a"] == fc["base_country"])).all()
    assert (fc["host_national_b"] == (fc["nationality_b"] == fc["base_country"])).all()
