"""Experiment runner: load a run (config/runs.csv) -> build trials -> plan -> call models -> raw JSONL.

Safety and integrity rules (design contract v0.2; adversarial review H3, M7, M8, L5, L10):

* any non-mock provider is refused unless ``allow_real_calls`` is set; with the
  flag, a real run is still refused when a selected model has no pinned
  ``revision`` or is ``status: unverified``, when ``git status --porcelain``
  lists modified or untracked files under src/, config/, prompts/ or stimuli/,
  or (vLLM) when the server does not serve the configured ``model_id``;
* run ids: mock-only runs must start with "mock", runs with a real model must
  not (the "mock*" data directories are git-ignored);
* ``data/raw/<run_id>/responses.jsonl`` is append-only; one record per call after
  all transport retries; failures are records, never dropped;
* only transport/API errors are retried within a call (A4); malformed, empty or
  refused outputs are terminal and never re-sampled. Calls whose only records
  are ``api_error`` are attempted again on resume (M7), with attempts counted
  across sessions, until ``retry.max_api_error_sessions`` api_error records exist
  for an id; then that api_error record is terminal and listed in the session (N7);
* calls run in a seeded shuffle within each model, models in contiguous windows
  (A5); ``execution_index`` is logged;
* technical stop rule (M8, nationality-blind): once a model has
  ``first_fraction`` of its planned calls answered, it is stopped if more than
  ``max_non_ok_share`` of them are non-ok; transport failures (api_error) count
  neither way (N6); recorded in the manifest;
* resuming requires the same identity: config hash, full model specs, the
  assembled prompt templates, SHA-256 of both stimulus tables (cvs.csv,
  nationalities.csv), the CV template, jobs.csv, principle_items.csv,
  prompt_parts.csv and prompt_recipes.csv, and the parser version (H3). The
  default run id contains a hash of this identity, so a changed input starts a
  new run;
* rendered prompts are stored once per SHA-256 in ``prompts.jsonl``;
  ``run_manifest.json`` holds the snapshot, provenance and one entry per session;
  ``fc_design.json`` stores the checked forced-choice design.
"""

from __future__ import annotations

import json
import math
import os
import random
import time
from collections import Counter, defaultdict
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .config import (ExperimentConfig, JobAd, ModelSpec, NationalitySet, PrincipleSpec, RunConfigError,
                     load_experiment_config, load_jobs, load_models, load_nationalities, load_principle_items,
                     load_run_config)
from .logging_utils import add_file_handler, get_logger, remove_handler
from .manifest import environment, package_root, uncommitted_paths
from .parse_outputs import parser_fingerprint
from .parsing import PARSER_VERSION, parse_response
from .paths import ProjectPaths
from .prompts import (PRINCIPLE_TEMPLATE_ID, SYSTEM_TEMPLATE_ID, PromptLibrary, PromptTemplate, load_library,
                      prompt_sha256, render_job_ad, template_id, validate_library)
from .providers import ChatRequest, NonRetryableProviderError, Provider, ProviderError, RetryableProviderError, make_provider
from .randomization import (PRIMARY_ARM, Call, StimulusRef, Trial, TrialPlan, all_stimuli, build_trials,
                            expand_calls, fc_design_summary)
from .stimuli.render import load_template as load_cv_template
from .stimuli.render import render_clone
from .tables import load_cv_table
from .utils import atomic_write_json, iter_jsonl, sha256_text_file, stable_hash, utc_now_iso

log = get_logger("runner")
MOCK_PREFIX = "mock"


class RealCallsNotAllowed(RuntimeError):
    pass


class RunConfigMismatch(RuntimeError):
    pass


class RunAborted(RuntimeError):
    pass


class RunIdPolicyError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# Loading an experiment
# --------------------------------------------------------------------------- #
@dataclass
class Experiment:
    cfg: ExperimentConfig
    config_source: str
    paths: ProjectPaths
    all_nationalities: NationalitySet
    nationality_codes: list[str]
    placebo_codes: set[str]
    jobs: dict[str, JobAd]
    models: dict[str, ModelSpec]
    occupations: list[str]
    principle: PrincipleSpec
    cvs: dict[str, dict]                 # cv_id -> row of stimuli/cvs.csv
    cv_template: str
    stimuli: list[StimulusRef]
    prompts: PromptLibrary                # prompts/prompt_parts.csv + prompt_recipes.csv
    templates: dict[str, PromptTemplate]  # the templates this run uses (template_id -> assembled recipe)
    plan: TrialPlan
    run_id: str = ""
    stimulus_problems: list[str] = field(default_factory=list)

    @property
    def config_hash(self) -> str:
        return self.cfg.config_hash()

    @property
    def is_mock(self) -> bool:
        return all(m.is_mock for m in self.models.values())

    def template_hashes(self) -> dict[str, str]:
        """SHA-256 of the system prompt and of every assembled user template this run uses."""
        out = {tid: t.sha256 for tid, t in self.templates.items()}
        out[SYSTEM_TEMPLATE_ID] = self.prompts.system_sha256
        return dict(sorted(out.items()))

    def input_file_hashes(self) -> dict[str, str]:
        """SHA-256 of the stimulus tables, the CV template, the job ads and the prompt tables."""
        p = self.paths
        files = (p.cv_table_file, p.nationalities_file, p.cv_template_file, p.jobs_file, p.principle_items_file,
                 p.prompt_parts_file, p.prompt_recipes_file)
        return {f.name: sha256_text_file(f) for f in files}

    def identity(self) -> dict:
        """Everything a resumed session must share with the first one (H3)."""
        return {"config_hash": self.config_hash,
                "models": {a: s.model_dump(mode="json") for a, s in sorted(self.models.items())},
                "prompt_templates": self.template_hashes(),
                "input_files": self.input_file_hashes(),
                "parser_version": PARSER_VERSION}

    def temperature(self, trial: Trial) -> float:
        return self.cfg.sampling.temperature if trial.temperature is None else trial.temperature


def _resolve_occupations(cfg: ExperimentConfig, jobs: dict[str, JobAd]) -> list[str]:
    if cfg.occupations == "all":
        return list(jobs)
    if cfg.occupations == "pilot":
        return [o for o, j in jobs.items() if j.pilot]
    unknown = set(cfg.occupations) - set(jobs)
    if unknown:
        raise KeyError(f"unknown occupations in config: {sorted(unknown)}")
    return list(cfg.occupations)


def resolve_run(run: str | dict, paths: ProjectPaths) -> tuple[ExperimentConfig, str]:
    """(config, source label) for a run name of config/runs.csv or a programmatic dict."""
    if isinstance(run, dict):
        return load_experiment_config(run), "<dict>"
    name = str(run)
    if name.endswith((".yaml", ".yml")) or "/" in name or "\\" in name:
        raise RunConfigError(f"{name!r} is not a run name: runs are the rows of config/runs.csv (the YAML "
                             f"experiment configs were removed); use a run name such as mock, pilot or main")
    return load_run_config(paths.runs_file, name), f"config/runs.csv:{name}"


def load_experiment(config: str | dict, paths: ProjectPaths | None = None, run_id: str | None = None,
                    validate_stimuli: bool = True) -> Experiment:
    """``config`` = a run name of config/runs.csv (mock, pilot, main) or a dict
    (programmatic config, merged over the code defaults)."""
    paths = paths or ProjectPaths.from_root()
    cfg, source = resolve_run(config, paths)
    all_nat = load_nationalities(paths.nationalities_file)
    codes = all_nat.codes if cfg.nationalities == "all" else all_nat.subset(list(cfg.nationalities)).codes
    placebo = {n.code for n in all_nat.conditions if n.group == "placebo" and n.code in codes}
    jobs = load_jobs(paths.jobs_file)
    registry = load_models(paths.models_file)
    arm_models = {m for a in cfg.robustness_arms if a.models != "all" for m in a.models}
    unknown = [m for m in [*cfg.models, *arm_models] if m not in registry]
    if unknown:
        raise KeyError(f"models not in {paths.models_file}: {unknown}")
    stray = arm_models - set(cfg.models)
    if stray:
        raise ValueError(f"robustness arms name models that are not in `models`: {sorted(stray)}")
    models = {m: registry[m] for m in cfg.models}
    if len({s.is_mock for s in models.values()}) > 1:
        raise ValueError("an experiment may not mix the mock provider with real models")
    occupations = _resolve_occupations(cfg, jobs)
    principle = load_principle_items(paths.principle_items_file, paths.prompt_parts_file)
    library = load_library(paths.prompts_dir)

    cvs = load_cv_table(paths.cv_table_file)
    stimuli = all_stimuli(cvs, codes, positive_control=True)
    cv_template = load_cv_template(paths.cv_template_file)

    problems: list[str] = []
    if validate_stimuli:
        from .validation import validate_stimuli as _validate

        # The runtime never reads the CV building blocks (title-bullet coherence is checked by validate-stimuli).
        problems += _validate(paths, check_prompts=True, use_pools=False).errors
    else:
        problems += [f"prompts: {p}" for p in validate_library(library, cfg.prompt_variants)]

    tids = set()
    for c in cfg.enabled_conditions():
        if c == "principle_probe":
            tids.add(PRINCIPLE_TEMPLATE_ID)
        else:
            tids |= {template_id(c, k) for k in cfg.prompt_variants}
    templates = {t: library.template(t) for t in sorted(tids)}

    plan = build_trials(cfg, stimuli, occupations, codes, principle, all_occupations=list(jobs),
                        placebo_codes=placebo)
    exp = Experiment(cfg=cfg, config_source=source,
                     paths=paths, all_nationalities=all_nat, nationality_codes=codes, placebo_codes=placebo,
                     jobs=jobs, models=models, occupations=occupations, principle=principle,
                     cvs={cv["cv_id"]: cv for cv in cvs}, cv_template=cv_template, stimuli=stimuli,
                     prompts=library, templates=templates, plan=plan, stimulus_problems=problems)
    exp.run_id = run_id or cfg.run_id or f"{cfg.experiment_id}__{stable_hash(exp.identity(), 8)}"
    return exp


# --------------------------------------------------------------------------- #
# Prompt rendering
# --------------------------------------------------------------------------- #
class PromptBuilder:
    """Builds prompts at call time: the trial's recipe (prompts/prompt_recipes.csv) with its
    slots filled: job ad + render(cv row, nationality row, clone type), or probe context + item."""

    def __init__(self, exp: Experiment):
        self.exp = exp
        self._by_id = {s.stimulus_id: s for s in exp.stimuli}
        self._items = exp.principle.by_id()

    def cv_text(self, sid: str) -> str:
        s = self._by_id[sid]
        demonym = self.exp.all_nationalities.by_code(s.nationality_code).demonym
        return render_clone(self.exp.cvs[s.cv_id], demonym, s.clone_type, self.exp.cv_template)

    def job_for(self, trial: Trial) -> JobAd:
        """The job ad localized to the base city of the trial's CV(s) (a forced-choice
        pair shares one base country)."""
        cvs = [self.exp.cvs[self._by_id[s].cv_id] for s in trial.stimulus_ids]
        bases = {(cv["base_country"], cv["base_city"]) for cv in cvs}
        if len(bases) != 1:
            raise ValueError(f"trial {trial.trial_id}: CVs with different base countries {sorted(bases)}")
        code, city = bases.pop()
        country = self.exp.all_nationalities.by_code(code).country
        return self.exp.jobs[trial.occupation].localize(city, country)

    def slot_values(self, trial: Trial) -> dict[str, str]:
        """The values of the recipe's slots (JOB_AD and CV, or JOB_AD, CV_A and CV_B, or
        CONTEXT and ITEM)."""
        if trial.task_type == "principle_probe":
            return {"CONTEXT": self.exp.principle.context_text(trial.context, self.exp.jobs),
                    "ITEM": self._items[trial.item_id].text}
        values = {"JOB_AD": render_job_ad(self.job_for(trial))}
        texts = [self.cv_text(s).rstrip("\n") for s in trial.stimulus_ids]
        if trial.task_type == "independent":
            values["CV"] = texts[0]
        else:
            values["CV_A"], values["CV_B"] = texts
        return values

    def messages(self, trial: Trial) -> list[dict]:
        return self.exp.templates[trial.template_id].render(self.slot_values(trial))

    def user_text(self, trial: Trial) -> str:
        return self.messages(trial)[1]["content"]


# --------------------------------------------------------------------------- #
# Plan
# --------------------------------------------------------------------------- #
def _group(t: Trial, placebo: set[str]) -> str:
    if t.arm != PRIMARY_ARM:
        return f"{t.prompt_condition}[{t.arm}]"
    if t.clone_type == "positive_control":
        return "baseline[positive_control]"
    if t.task_type == "independent" and t.nationalities and t.nationalities[0] in placebo:
        return "baseline[placebo]"
    return t.prompt_condition


@dataclass
class PlanReport:
    experiment_id: str
    run_id: str
    config_hash: str
    calls: dict[tuple[str, str], int]
    input_chars: dict[tuple[str, str], int]
    groups: list[str]
    models: dict[str, ModelSpec]
    expected_output_tokens: int
    max_tokens: int
    n_trials: int
    fc_summary: dict
    stimulus_problems: list[str]
    placebo_codes: list[str]

    @property
    def total_calls(self) -> int:
        return sum(self.calls.values())

    def calls_by_model(self) -> dict[str, int]:
        out: Counter = Counter()
        for (m, _), n in self.calls.items():
            out[m] += n
        return dict(out)

    def format(self) -> str:
        g = self.groups
        w = max(10, *(len(m) for m in self.models))
        cw = [max(len(x), 7) for x in g]
        lines = [f"Plan for experiment '{self.experiment_id}'  (run_id {self.run_id}, config hash {self.config_hash[:12]})",
                 f"Unique trials: {self.n_trials}; the counts below include repetitions.", "",
                 "Calls by model x condition:",
                 f"{'model':<{w}} " + " ".join(f"{x:>{c}}" for x, c in zip(g, cw)) + f" {'total':>9}"]
        for m in self.models:
            row = [self.calls.get((m, x), 0) for x in g]
            lines.append(f"{m:<{w}} " + " ".join(f"{v:>{c}}" for v, c in zip(row, cw)) + f" {sum(row):>9}")
        tot = [sum(self.calls.get((m, x), 0) for m in self.models) for x in g]
        lines.append(f"{'TOTAL':<{w}} " + " ".join(f"{v:>{c}}" for v, c in zip(tot, cw)) + f" {sum(tot):>9}")
        if self.placebo_codes:
            lines.append(f"baseline[placebo] = placebo nationalities {self.placebo_codes} (baseline, primary arm only)")
        lines += ["", "Approximate tokens -- ROUGH: characters / 4 heuristic; real tokenizers differ, often by "
                      "20-30% or more:",
                  f"{'model':<{w}} {'input_tok':>13} {'output_tok(expected)':>22} {'output_tok(max)':>16}"]
        for m in self.models:
            n = sum(self.calls.get((m, x), 0) for x in g)
            chars = sum(self.input_chars.get((m, x), 0) for x in g)
            lines.append(f"{m:<{w}} {chars // 4:>13,} {n * self.expected_output_tokens:>22,} {n * self.max_tokens:>16,}")
        lines.append(f"(expected output = {self.expected_output_tokens} tokens/call; max = max_tokens "
                     f"{self.max_tokens}/call)")
        if self.fc_summary.get("n_quads"):
            s = self.fc_summary
            lines += ["", f"Forced-choice design: {s['n_quads']} quads per FC condition and model, "
                          f"{s['n_distinct_pairs']} distinct nationality pairs over {len(s['levels'])} levels, "
                          f"each level in {s['appearances_per_level']} quads, connected={s['connected']}, "
                          f"quads per variant {s['quads_per_variant']}, per-level variant spread "
                          f"{s['variant_spread_per_level']}"]
        lines.append("")
        for m, spec in self.models.items():
            flag = "mock (no network)" if spec.is_mock else f"REAL provider '{spec.provider}', status {spec.status}"
            lines.append(f"  {m}: {spec.model_id} (revision {spec.revision}) -- {flag}")
        if any(not s.is_mock for s in self.models.values()):
            lines.append("Real calls require --allow-real-calls, pinned revisions and a committed working tree.")
        if self.stimulus_problems:
            lines.append(f"WARNING: {len(self.stimulus_problems)} stimulus/prompt validation problem(s); "
                         f"run validate-stimuli.")
        return "\n".join(lines)


def make_plan(exp: Experiment) -> PlanReport:
    builder = PromptBuilder(exp)
    calls: Counter = Counter()
    chars: Counter = Counter()
    sys_len = len(exp.prompts.system_text)
    groups: list[str] = []
    for t in exp.plan.trials:
        key = (t.model_alias, _group(t, exp.placebo_codes))
        if key[1] not in groups:
            groups.append(key[1])
        calls[key] += t.repetitions
        chars[key] += (sys_len + len(builder.user_text(t))) * t.repetitions
    return PlanReport(experiment_id=exp.cfg.experiment_id, run_id=exp.run_id, config_hash=exp.config_hash,
                      calls=dict(calls), input_chars=dict(chars), groups=groups, models=exp.models,
                      expected_output_tokens=exp.cfg.plan.expected_output_tokens,
                      max_tokens=exp.cfg.sampling.max_tokens, n_trials=len(exp.plan.trials),
                      fc_summary=fc_design_summary(exp.plan.fc_design), stimulus_problems=exp.stimulus_problems,
                      placebo_codes=sorted(exp.placebo_codes) if exp.cfg.include_placebo else [])


# --------------------------------------------------------------------------- #
# Raw storage
# --------------------------------------------------------------------------- #
class JsonlAppender:
    """Single-writer, append-only JSONL file (flush per line, fsync periodically)."""

    def __init__(self, path: Path, fsync_every: int = 50):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        # A partial last line from a crash stays in the file (the parser reports
        # it); new records start on a fresh line.
        if path.exists() and path.stat().st_size > 0:
            with open(path, "rb") as fh:
                fh.seek(-1, os.SEEK_END)
                last = fh.read(1)
            if last != b"\n":
                with open(path, "ab") as fh:
                    fh.write(b"\n")
        self._fh = open(path, "a", encoding="utf-8", newline="\n")
        self._n = 0
        self._every = fsync_every

    def write(self, obj: dict) -> None:
        self._fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
        self._fh.flush()
        self._n += 1
        if self._n % self._every == 0:
            os.fsync(self._fh.fileno())

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.flush()
            os.fsync(self._fh.fileno())
            self._fh.close()


@dataclass
class ExistingRecords:
    done: set[str]                                 # terminal record_ids: a non-api_error record, or api_error cap reached
    api_error_attempts: dict[str, int]             # record_ids still to re-attempt -> transport attempts so far
    api_error_terminal: set[str]                   # record_ids whose api_error re-attempts are exhausted (N7)
    status_by_id: dict[str, str]                   # latest status per record_id (for the stop rule)
    model_by_id: dict[str, str]
    corrupt: int


def read_existing(path: Path, max_api_error_sessions: int = 3) -> ExistingRecords:
    """Terminal vs re-attemptable record_ids. A record_id with only api_error
    records is re-attempted in later sessions until it has
    ``max_api_error_sessions`` api_error records; then its last api_error record
    is terminal (review N7)."""
    done: set[str] = set()
    err_attempts: dict[str, int] = defaultdict(int)
    err_records: Counter = Counter()
    status: dict[str, str] = {}
    model: dict[str, str] = {}
    corrupt = 0
    if path.exists():
        for _, obj, _ in iter_jsonl(path):
            if obj is None or "record_id" not in obj:
                corrupt += 1
                continue
            rid = obj["record_id"]
            model[rid] = obj.get("model_alias")
            if obj.get("parse_status") == "api_error":
                err_attempts[rid] += int(obj.get("attempts") or 0) - int(obj.get("prior_attempts") or 0)
                err_records[rid] += 1
                status.setdefault(rid, "api_error")
            else:
                done.add(rid)
                status[rid] = obj.get("parse_status")
    terminal = {r for r, n in err_records.items() if r not in done and n >= max_api_error_sessions}
    pending = {r: n for r, n in err_attempts.items() if r not in done and r not in terminal}
    return ExistingRecords(done | terminal, pending, terminal, status, model, corrupt)


def existing_prompt_hashes(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {obj["prompt_sha256"] for _, obj, _ in iter_jsonl(path) if obj and "prompt_sha256" in obj}


# --------------------------------------------------------------------------- #
# Calling
# --------------------------------------------------------------------------- #
@dataclass
class CallOutcome:
    call: Call
    messages: list[dict]
    prompt_sha256: str
    temperature: float
    response: object | None
    api_error: dict | None
    attempts: int
    attempt_errors: list[dict]
    finished_utc: str


def _backoff(cfg: ExperimentConfig, attempt: int) -> float:
    base = cfg.retry.backoff_base_s
    if base <= 0:
        return 0.0
    return min(cfg.retry.backoff_max_s, base * 2 ** (attempt - 1)) * (0.5 + random.random() / 2)


def execute_call(exp: Experiment, provider: Provider, builder: PromptBuilder, call: Call) -> CallOutcome:
    """One call with transport-level retries only (A4)."""
    cfg, spec = exp.cfg, exp.models[call.trial.model_alias]
    messages = builder.messages(call.trial)
    s = cfg.sampling
    temperature = exp.temperature(call.trial)
    req = ChatRequest(messages=messages, temperature=temperature, top_p=s.top_p, max_tokens=s.max_tokens,
                      seed=call.seed if spec.supports_seed else None,
                      json_mode=s.json_mode and spec.supports_json_mode,
                      want_logprobs=s.logprobs and spec.supports_logprobs,
                      top_logprobs=s.top_logprobs, logprobs_max_tokens=s.logprobs_max_tokens,
                      extra_params=dict(s.openai_compatible_extra) if spec.provider == "openai_compatible" else {})
    errors: list[dict] = []
    response = api_error = None
    attempt = 0
    for attempt in range(1, cfg.retry.max_attempts + 1):
        try:
            response = provider.complete(req)
            break
        except RetryableProviderError as e:
            errors.append({**e.to_record(), "attempt": attempt, "utc": utc_now_iso()})
            if attempt == cfg.retry.max_attempts:
                api_error = {**e.to_record(), "reason": "transport retries exhausted"}
                break
            time.sleep(_backoff(cfg, attempt))
        except (NonRetryableProviderError, ProviderError) as e:
            errors.append({**e.to_record(), "attempt": attempt, "utc": utc_now_iso()})
            api_error = e.to_record()
            break
        except Exception as e:  # unexpected provider bug: record it, never drop the call
            rec = {"type": type(e).__name__, "message": str(e)[:2000], "status_code": None, "retryable": False,
                   "unexpected": True}
            errors.append({**rec, "attempt": attempt, "utc": utc_now_iso()})
            api_error = rec
            break
    return CallOutcome(call, messages, prompt_sha256(messages), temperature, response, api_error, attempt, errors,
                       utc_now_iso())


def build_record(exp: Experiment, outcome: CallOutcome, prior_attempts: int = 0) -> dict:
    cfg, call, t = exp.cfg, outcome.call, outcome.call.trial
    spec = exp.models[t.model_alias]
    resp = outcome.response
    s = cfg.sampling
    if outcome.api_error is not None or resp is None:
        raw_output, parse_status, parsed, parse_errors, refusal = None, "api_error", None, [], False
    else:
        raw_output = resp.text
        pr = parse_response(raw_output, t.task_type)
        parse_status, parsed, parse_errors, refusal = pr.parse_status, pr.extracted, pr.errors, pr.refusal
    item = exp.principle.by_id().get(t.item_id) if t.item_id else None
    return {
        "record_id": call.record_id,
        "trial_id": t.trial_id,
        "run_id": exp.run_id,
        "experiment_id": cfg.experiment_id,
        "config_hash": exp.config_hash,
        "timestamp_utc": outcome.finished_utc,
        "provider": spec.provider,
        "model_id": spec.model_id,
        "model_alias": spec.alias,
        "temperature": outcome.temperature,
        "top_p": s.top_p,
        "max_tokens": s.max_tokens,
        "seed": call.seed if spec.supports_seed else None,
        "system_prompt_version": exp.prompts.system_version,
        "user_prompt_version": exp.templates[t.template_id].version,
        "prompt_condition": t.prompt_condition,
        "task_type": t.task_type,
        "occupation": t.occupation,
        "repetition": call.repetition,
        "stimulus_ids": list(t.stimulus_ids),
        "base_cv_ids": list(t.base_cv_ids),
        "nationalities": list(t.nationalities),
        "qualification_tier": t.qualification_tier,
        "fc_order": t.fc_order,
        "quad_id": t.quad_id,
        "prompt_sha256": outcome.prompt_sha256,
        "raw_output": raw_output,
        "finish_reason": getattr(resp, "finish_reason", None),
        "usage": getattr(resp, "usage", None),
        "latency_ms": getattr(resp, "latency_ms", None),
        "logprobs": getattr(resp, "logprobs", None),
        "parsed": parsed,
        "parse_status": parse_status,
        "refusal": refusal,
        "api_error": outcome.api_error,
        "attempts": prior_attempts + outcome.attempts,      # transport attempts, across sessions (M7)
        "is_mock": spec.is_mock,
        # --- v0.2 (A18) ---
        "prompt_variant": t.prompt_variant,
        "execution_index": call.execution_index,
        "model_revision": spec.revision,
        "clone_type": t.clone_type,
        # --- setting (user request 2026-10-01) ---
        "base_country": t.base_country,
        "host_national": ([code == t.base_country for code in t.nationalities] if t.base_country else None),
        # --- additional provenance ---
        "prior_attempts": prior_attempts,
        "transport_retries": max(0, outcome.attempts - 1),
        "arm": t.arm,
        "item_id": t.item_id,
        "context": t.context,
        "keying": item.keying if item else None,
        "item_type": item.item_type if item else None,
        "json_mode": s.json_mode and spec.supports_json_mode,
        "model_status": spec.status,
        "request_params": getattr(resp, "request_params", None),
        "response_metadata": getattr(resp, "raw_metadata", None),
        "attempt_errors": outcome.attempt_errors,
        "parse_errors": parse_errors,
        "parser_version": PARSER_VERSION,
    }


# --------------------------------------------------------------------------- #
# Guards
# --------------------------------------------------------------------------- #
def check_run_id_policy(exp: Experiment) -> None:
    """L5: mock runs must start with "mock" (git-ignored), real runs must not."""
    starts = exp.run_id.lower().startswith(MOCK_PREFIX)
    if exp.is_mock and not starts:
        raise RunIdPolicyError(f"mock run id {exp.run_id!r} must start with '{MOCK_PREFIX}' "
                               f"(mock outputs are git-ignored by that prefix)")
    if not exp.is_mock and starts:
        raise RunIdPolicyError(f"real run id {exp.run_id!r} must not start with '{MOCK_PREFIX}' (it would be "
                               f"git-ignored and the evidence lost)")


def preflight_real_calls(exp: Experiment, selected: list[str]) -> None:
    """H3: refuse unpinned/unverified models and an uncommitted working tree."""
    problems = []
    for alias in selected:
        spec = exp.models[alias]
        if spec.is_mock:
            continue
        if not spec.revision:
            problems.append(f"model {alias}: `revision` is empty in config/models.csv (pin the HF commit SHA "
                            f"or dated API snapshot)")
        if spec.status == "unverified":
            problems.append(f"model {alias}: status is 'unverified' (pin and verify the model id first)")
    # Both the data root (--root) and the repository holding the imported code (N2).
    roots = {"data root": Path(exp.paths.root).resolve(), "code (hiringaudit package)": package_root()}
    for label, root in roots.items():
        if label != "data root" and root == roots["data root"]:
            continue
        dirty = uncommitted_paths(root)
        if dirty is None:
            problems.append(f"{label} {root}: cannot verify the git state (git unavailable or not a work tree); "
                            f"commit the code first")
        elif dirty:
            problems.append(f"{label} {root}: {len(dirty)} modified or untracked file(s) under src/, config/, "
                            f"prompts/, stimuli/ (e.g. {dirty[:3]}); commit before a real run")
    if problems:
        raise RealCallsNotAllowed("refusing real calls:\n  - " + "\n  - ".join(problems))


def check_served_models(exp: Experiment, providers: dict[str, Provider], observed: dict[str, dict]) -> None:
    """H3: for vLLM, the server must actually serve the configured model_id."""
    for alias, prov in providers.items():
        spec = exp.models[alias]
        if spec.provider != "openai_compatible":
            continue
        served = [m.get("id") for m in (observed.get(alias, {}).get("server", {}).get("served_models") or [])]
        if spec.model_id not in served:
            raise RealCallsNotAllowed(f"model {alias}: the server at {observed.get(alias, {}).get('server', {}).get('endpoint')} "
                                      f"serves {served or 'nothing (no answer from /v1/models)'}, not {spec.model_id!r}")


# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
@dataclass
class RunOptions:
    allow_real_calls: bool = False
    limit: int | None = None
    models: list[str] | None = None
    workers: int | None = None
    show_progress: bool = True


@dataclass
class RunSummary:
    run_id: str
    raw_dir: Path
    planned: int
    already_recorded: int
    written: int
    status: str
    parse_status_counts: dict
    stopped_models: dict = field(default_factory=dict)


def _check_or_create_manifest(exp: Experiment, raw_dir: Path) -> dict:
    path = raw_dir / "run_manifest.json"
    ident = exp.identity()
    if path.exists():
        man = json.loads(path.read_text(encoding="utf-8"))
        diffs = []
        for k, v in ident.items():
            old = man.get("identity", {}).get(k)
            if old != v:
                if isinstance(v, dict) and isinstance(old, dict):
                    sub = sorted(x for x in set(v) | set(old) if v.get(x) != old.get(x))
                    diffs.append(f"{k} ({', '.join(sub)})")
                else:
                    diffs.append(k)
        if diffs:
            raise RunConfigMismatch(
                f"run {exp.run_id} was started with different inputs: {'; '.join(diffs)}. Refusing to mix them in "
                f"one run. Use a new run id (the default run id already changes with these inputs).")
        return man
    return {
        "run_id": exp.run_id,
        "experiment_id": exp.cfg.experiment_id,
        "is_mock": exp.is_mock,
        "WARNING": "SYNTHETIC MOCK DATA - NOT RESULTS" if exp.is_mock else None,
        "created_utc": utc_now_iso(),
        "config_source": exp.config_source,
        "identity": ident,
        "config_hash": exp.config_hash,
        "prompt_templates": exp.template_hashes(),
        "parser_version": PARSER_VERSION,
        "parser_fingerprint": parser_fingerprint(exp.paths.text_flags_file),
        "config_snapshot": exp.cfg.model_dump(mode="json"),
        "models": {a: s.model_dump(mode="json") for a, s in exp.models.items()},
        "model_provenance": {a: s.provenance() for a, s in exp.models.items()},
        "input_file_sha256": exp.input_file_hashes(),
        "placebo_nationalities": sorted(exp.placebo_codes) if exp.cfg.include_placebo else [],
        "seeds": {"master": exp.cfg.seed,
                  "call_seed": "derive_int(master, 'call', model, arm, condition, sorted base CVs, variant, "
                               "fc_order, item, context, repetition) -- never nationality (A17)",
                  "execution_order": "seeded shuffle within model, models contiguous in config order (A5)"},
        "n_trials": len(exp.plan.trials),
        "n_planned_calls": sum(t.repetitions for t in exp.plan.trials),
        "fc_design_summary": fc_design_summary(exp.plan.fc_design),
        "stop_rule": {"config": exp.cfg.stop_rule.model_dump(), "models": {}},
        "sessions": [],
    }


def run_experiment(exp: Experiment, options: RunOptions | None = None, provider_factory=None) -> RunSummary:
    options = options or RunOptions()
    selected = [a for a in exp.models if not options.models or a in options.models]
    real = [a for a in selected if not exp.models[a].is_mock]
    if real and not options.allow_real_calls:
        raise RealCallsNotAllowed(f"refusing to call real provider(s) for {real} without --allow-real-calls "
                                  f"(review the plan first)")
    check_run_id_policy(exp)
    if real:
        preflight_real_calls(exp, real)
    if exp.stimulus_problems:
        raise RuntimeError("stimulus/prompt validation failed; run `python -m hiringaudit validate-stimuli`:\n  "
                           + "\n  ".join(exp.stimulus_problems[:20]))
    fc = fc_design_summary(exp.plan.fc_design)
    if exp.plan.fc_design and (not fc["connected"] or len(fc["appearances_per_level"]) != 1):
        raise RuntimeError(f"forced-choice design failed its balance/connectivity check: {fc}")

    raw_dir = exp.paths.raw_run_dir(exp.run_id)
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest = _check_or_create_manifest(exp, raw_dir)
    if exp.plan.fc_design and not (raw_dir / "fc_design.json").exists():
        atomic_write_json(raw_dir / "fc_design.json", {"summary": fc, "quads": [asdict(q) for q in exp.plan.fc_design]})
    handler = add_file_handler(raw_dir / "run.log")
    responses = raw_dir / "responses.jsonl"
    existing = read_existing(responses, exp.cfg.retry.max_api_error_sessions)
    if existing.corrupt:
        log.warning("%d corrupt line(s) in %s (kept; their calls will be redone)", existing.corrupt, responses)

    all_calls = expand_calls(exp.plan.trials, exp.run_id, exp.cfg.seed, exp.cfg.models)
    planned_per_model = Counter(c.trial.model_alias for c in all_calls)
    stop_state = manifest.setdefault("stop_rule", {"config": exp.cfg.stop_rule.model_dump(), "models": {}})["models"]
    stopped = {a for a, st in stop_state.items() if st.get("stopped")}
    for a in stopped & set(selected):
        log.warning("model %s was stopped by the technical stop rule earlier in this run; skipping it", a)
    in_scope = [c for c in all_calls if c.trial.model_alias in selected]
    todo = [c for c in in_scope if c.record_id not in existing.done and c.trial.model_alias not in stopped]
    already = sum(1 for c in in_scope if c.record_id in existing.done)
    if options.limit is not None:
        todo = todo[: options.limit]

    factory = provider_factory or (lambda spec: make_provider(spec, exp.cfg.mock, exp.all_nationalities, exp.principle))
    providers: dict[str, Provider] = {}
    observed: dict[str, dict] = {}
    try:
        for alias in dict.fromkeys(c.trial.model_alias for c in todo):
            providers[alias] = factory(exp.models[alias])
            providers[alias].check_ready()
            observed[alias] = {**exp.models[alias].provenance(), "server": providers[alias].introspect()}
        if real:
            check_served_models(exp, {a: p for a, p in providers.items() if a in real}, observed)
    except BaseException:
        remove_handler(handler)
        raise

    session = {"started_utc": utc_now_iso(),
               "options": {"limit": options.limit, "models": options.models,
                           "workers": options.workers or exp.cfg.workers, "allow_real_calls": options.allow_real_calls},
               "environment": environment(exp.paths.root), "model_provenance_observed": observed,
               "n_existing_terminal_records": len(existing.done),
               "n_api_error_retries_pending": len(existing.api_error_attempts),
               "api_error_terminal": sorted(existing.api_error_terminal), "n_to_call": len(todo)}
    manifest["sessions"].append(session)
    atomic_write_json(raw_dir / "run_manifest.json", manifest)
    log.info("run %s: %d planned calls in scope, %d already recorded, %d to call now",
             exp.run_id, len(in_scope), already, len(todo))

    # --- stop-rule bookkeeping (nationality-blind: only parse-status counts) ---
    sr = exp.cfg.stop_rule
    seen_status: dict[str, dict[str, str]] = defaultdict(dict)
    for rid, st in existing.status_by_id.items():
        seen_status[existing.model_by_id.get(rid)][rid] = st
    threshold = {m: max(1, math.ceil(sr.first_fraction * n)) for m, n in planned_per_model.items()}
    newly_stopped: dict[str, dict] = {}

    def evaluate_stop(model: str) -> None:
        # transport failures (api_error) are excluded from numerator and denominator (review N6)
        answered = [s for s in seen_status[model].values() if s != "api_error"]
        if not sr.enabled or model in stop_state or len(answered) < threshold[model]:
            return
        n = len(answered)
        non_ok = sum(1 for s in answered if s != "ok")
        share = non_ok / n
        verdict = {"evaluated_at_n": n, "threshold_n": threshold[model], "non_ok": non_ok,
                   "non_ok_share": round(share, 4), "max_non_ok_share": sr.max_non_ok_share,
                   "stopped": share > sr.max_non_ok_share, "utc": utc_now_iso()}
        stop_state[model] = verdict
        if verdict["stopped"]:
            stopped.add(model)
            newly_stopped[model] = verdict
            log.warning("TECHNICAL STOP: model %s has %.1f%% non-ok responses in its first %d calls (> %.0f%%); "
                        "its remaining calls are skipped", model, 100 * share, n, 100 * sr.max_non_ok_share)
        atomic_write_json(raw_dir / "run_manifest.json", manifest)

    for m in list(seen_status):
        if m in planned_per_model:
            evaluate_stop(m)

    builder = PromptBuilder(exp)
    writer = JsonlAppender(responses)
    prompt_writer = JsonlAppender(raw_dir / "prompts.jsonl")
    seen_prompts = existing_prompt_hashes(raw_dir / "prompts.jsonl")
    counts: Counter = Counter()
    written = 0
    consecutive_errors = 0
    status = "completed"
    progress = None
    if options.show_progress and todo:
        try:
            from tqdm import tqdm

            progress = tqdm(total=len(todo), unit="call", desc=exp.run_id, leave=False)
        except ImportError:  # pragma: no cover
            progress = None

    def handle(outcome: CallOutcome) -> None:
        nonlocal written, consecutive_errors
        rid = outcome.call.record_id
        rec = build_record(exp, outcome, prior_attempts=existing.api_error_attempts.get(rid, 0))
        if outcome.prompt_sha256 not in seen_prompts:
            prompt_writer.write({"prompt_sha256": outcome.prompt_sha256, "messages": outcome.messages,
                                 "system_prompt_version": rec["system_prompt_version"],
                                 "user_prompt_version": rec["user_prompt_version"]})
            seen_prompts.add(outcome.prompt_sha256)
        writer.write(rec)
        written += 1
        counts[rec["parse_status"]] += 1
        model = outcome.call.trial.model_alias
        if seen_status[model].get(rid) in (None, "api_error"):
            seen_status[model][rid] = rec["parse_status"]
        evaluate_stop(model)
        consecutive_errors = consecutive_errors + 1 if rec["parse_status"] == "api_error" else 0
        if progress is not None:
            progress.update(1)
        if consecutive_errors >= exp.cfg.retry.max_consecutive_api_errors:
            raise RunAborted(f"{consecutive_errors} consecutive API errors; aborting this session (records so far "
                             f"are kept; fix the endpoint and re-run to resume)")

    def handle_batch(futures) -> None:
        """Handle every finished future, even if one raises RunAborted (L10)."""
        abort = None
        for fut in futures:
            try:
                handle(fut.result())
            except RunAborted as e:
                abort = abort or e
        if abort:
            raise abort

    workers = options.workers or exp.cfg.workers
    try:
        if workers <= 1:
            for call in todo:
                if call.trial.model_alias in stopped:
                    continue
                handle(execute_call(exp, providers[call.trial.model_alias], builder, call))
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                pending: set[Future] = set()
                it = iter(todo)
                exhausted = False
                try:
                    while True:
                        while not exhausted and len(pending) < workers * 2:
                            call = next(it, None)
                            if call is None:
                                exhausted = True
                                break
                            if call.trial.model_alias in stopped:
                                continue
                            pending.add(pool.submit(execute_call, exp, providers[call.trial.model_alias], builder, call))
                        if not pending:
                            break
                        finished, pending = wait(pending, return_when=FIRST_COMPLETED)
                        handle_batch(finished)
                except BaseException:
                    for fut in pending:
                        fut.cancel()
                    done_ok = [f for f in pending if f.done() and not f.cancelled() and f.exception() is None]
                    try:
                        handle_batch(done_ok)  # never lose a call that already finished
                    except RunAborted:
                        pass
                    raise
    except KeyboardInterrupt:
        status = "interrupted"
        raise
    except RunAborted:
        status = "aborted"
        raise
    except BaseException:
        status = "failed"
        raise
    finally:
        if progress is not None:
            progress.close()
        writer.close()
        prompt_writer.close()
        session.update({"ended_utc": utc_now_iso(), "status": status, "n_written": written,
                        "parse_status_counts": dict(counts), "stopped_models": newly_stopped})
        atomic_write_json(raw_dir / "run_manifest.json", manifest)
        log.info("run %s session %s: wrote %d records %s", exp.run_id, status, written, dict(counts))
        remove_handler(handler)
    return RunSummary(exp.run_id, raw_dir, len(in_scope), already, written, status, dict(counts),
                      {a: v for a, v in stop_state.items() if v.get("stopped")})


def coverage(exp: Experiment) -> dict:
    """Planned vs recorded record_ids for a run (api_error-only ids are counted separately)."""
    planned = {c.record_id for c in expand_calls(exp.plan.trials, exp.run_id, exp.cfg.seed, exp.cfg.models)}
    path = exp.paths.raw_run_dir(exp.run_id) / "responses.jsonl"
    recs = [obj for _, obj, _ in iter_jsonl(path) if obj] if path.exists() else []
    terminal = Counter(r["record_id"] for r in recs if r["parse_status"] != "api_error")
    any_rec = {r["record_id"] for r in recs}
    return {"planned": len(planned), "records": len(recs), "record_ids": len(any_rec),
            "missing": len(planned - any_rec), "api_error_only": len(any_rec - set(terminal)),
            "unexpected": len(any_rec - planned), "duplicates": sum(1 for n in terminal.values() if n > 1),
            "parse_status": dict(Counter(r["parse_status"] for r in recs))}
