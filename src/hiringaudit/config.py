"""Loading and validating the input tables (all CSV; conventions in DATA_FORMAT.md).

* ``stimuli/nationalities.csv``    - factor N (see ``tables.py``)
* ``stimuli/cvs.csv``              - the base CVs (see ``tables.py``)
* ``stimuli/jobs.csv``             - factor J and the job ads (one row per occupation)
* ``config/models.csv``            - model registry (+ provenance fields), one row per model
* ``config/runs.csv``              - one row per run (mock, pilot, main), every setting a column
* ``config/text_flags.csv``        - patterns of the exploratory reason-text flags
* ``prompts/principle_items.csv``  - principle-probe statements (contexts: prompts/prompt_parts.csv)
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from . import csvio
from .utils import stable_hash

PROMPT_CONDITIONS = ("baseline", "neutrality", "forced_choice", "forced_choice_neutrality", "principle_probe")
INDEPENDENT_CONDITIONS = ("baseline", "neutrality")
FC_CONDITIONS = ("forced_choice", "forced_choice_neutrality")
TIERS = ("strong", "adequate", "borderline")


# --------------------------------------------------------------------------- #
# Nationalities
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Nationality:
    code: str
    country: str | None
    demonym: str | None
    group: str
    subregion: str
    arab_identity_contested: bool
    arab_league_joined: int | None = None
    note: str = ""


@dataclass(frozen=True)
class NationalitySet:
    reference: str
    conditions: tuple[Nationality, ...]

    @property
    def codes(self) -> list[str]:
        return [n.code for n in self.conditions]

    def by_code(self, code: str) -> Nationality:
        for n in self.conditions:
            if n.code == code:
                return n
        raise KeyError(f"unknown nationality code: {code}")

    def demonym_to_code(self) -> dict[str, str]:
        return {n.demonym: n.code for n in self.conditions if n.demonym}

    def subset(self, codes: list[str]) -> "NationalitySet":
        unknown = set(codes) - set(self.codes)
        if unknown:
            raise KeyError(f"unknown nationality codes: {sorted(unknown)}")
        return NationalitySet(self.reference, tuple(n for n in self.conditions if n.code in codes))


def load_nationalities(path: str | Path) -> NationalitySet:
    """Read ``stimuli/nationalities.csv``."""
    from .tables import load_nationalities as _load

    return _load(path)


# --------------------------------------------------------------------------- #
# Jobs
# --------------------------------------------------------------------------- #
JOB_LOCATION_PLACEHOLDER = "{city}, {country}"


class JobAd(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    pilot: bool
    skill_level: str
    customer_contact: str
    trust_role: str
    fit_emphasis: str
    required_years: int
    title: str
    employer: str
    location: str
    about: str
    tasks: list[str]
    requirements: list[str]
    positive_control_requirement: str
    offer: list[str]

    @model_validator(mode="after")
    def _consistent(self) -> "JobAd":
        if self.positive_control_requirement not in self.requirements:
            raise ValueError(f"{self.id}: positive_control_requirement must be one of the requirements")
        if not any(f"At least {self.required_years} years" in r for r in self.requirements):
            raise ValueError(f"{self.id}: no requirement states 'At least {self.required_years} years'")
        if self.location != JOB_LOCATION_PLACEHOLDER:
            raise ValueError(f"{self.id}: location must be {JOB_LOCATION_PLACEHOLDER!r} (the ad is located in the "
                             f"base city of the CV it is shown with)")
        return self

    def localize(self, city: str, country: str) -> "JobAd":
        """The ad as shown with a CV set in ``city``, ``country``: the placeholders
        ``{city}`` and ``{country}`` are filled in every text field; nothing else
        changes, so the ads of one occupation differ only in their location."""
        def fill(s: str) -> str:
            return s.replace("{city}", city).replace("{country}", country)

        return self.model_copy(update={
            "location": fill(self.location), "about": fill(self.about), "tasks": [fill(t) for t in self.tasks],
            "requirements": [fill(r) for r in self.requirements],
            "positive_control_requirement": fill(self.positive_control_requirement),
            "offer": [fill(o) for o in self.offer]})


JOB_COLUMNS = ("occupation", "pilot", "title", "employer", "location", "about", "tasks", "requirements",
               "positive_control_requirement", "offer", "required_years", "skill_level", "customer_contact",
               "trust_role", "fit_emphasis")
JOB_LIST_COLUMNS = ("tasks", "requirements", "offer")


def load_jobs(path: str | Path) -> dict[str, JobAd]:
    """Read ``stimuli/jobs.csv`` (one row per occupation, in row order)."""
    jobs: dict[str, JobAd] = {}
    for r in csvio.read_rows(path, JOB_COLUMNS, allowed=JOB_COLUMNS):
        occ = csvio.text(r["occupation"])
        at = csvio.where(path, occ)
        if not occ or occ in jobs:
            raise csvio.TableError(f"{at}: occupation is empty or duplicated")
        spec = {c: csvio.text(r[c]) for c in JOB_COLUMNS if c not in ("occupation", "pilot", "required_years",
                                                                       *JOB_LIST_COLUMNS)}
        spec.update({c: csvio.items(r[c]) for c in JOB_LIST_COLUMNS})
        try:
            jobs[occ] = JobAd(id=occ, pilot=csvio.boolean(r["pilot"], at),
                              required_years=csvio.integer(r["required_years"], at), **spec)
        except ValidationError as e:
            raise csvio.TableError(f"{at}: {e}") from e
    return jobs


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
ProviderName = Literal["mock", "openai_compatible", "openai", "anthropic", "google", "hf_local"]
PROVENANCE_FIELDS = ("model_id", "revision", "chat_template_sha256", "serving_engine",
                     "serving_engine_version", "dtype", "quantization", "gpu_type")


class ModelSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alias: str
    provider: ProviderName
    model_id: str
    status: Literal["ok", "candidate", "unverified"] = "unverified"
    supports_seed: bool = False
    supports_logprobs: bool = False
    supports_json_mode: bool = False
    base_url_env: str | None = None
    api_key_env: str | None = None
    extra_body: dict[str, Any] = Field(default_factory=dict)
    send_top_p: bool = True
    timeout_s: float = 120.0
    notes: str | None = None
    # --- provenance (A6): null when unknown, never guessed ---
    revision: str | None = None                # HF commit SHA or dated API snapshot
    chat_template_sha256: str | None = None
    serving_engine: str | None = None          # e.g. "vllm"
    serving_engine_version: str | None = None
    dtype: str | None = None
    quantization: str | None = None
    gpu_type: str | None = None

    @property
    def is_mock(self) -> bool:
        return self.provider == "mock"

    def provenance(self) -> dict:
        return {k: getattr(self, k) for k in PROVENANCE_FIELDS}


MODEL_COLUMNS = ("alias", "provider", "model_id", "revision", "status", "supports_seed", "supports_logprobs",
                 "supports_json_mode", "send_top_p", "timeout_s", "extra_body", "base_url_env", "api_key_env",
                 "serving_engine", "serving_engine_version", "dtype", "quantization", "gpu_type",
                 "chat_template_sha256", "notes")
_MODEL_BOOLS = ("supports_seed", "supports_logprobs", "supports_json_mode", "send_top_p")


def load_models(path: str | Path) -> dict[str, ModelSpec]:
    """Read ``config/models.csv`` (one row per model alias). Empty cells are null
    (unknown provenance is never guessed); ``extra_body`` is a JSON object."""
    models: dict[str, ModelSpec] = {}
    for r in csvio.read_rows(path, MODEL_COLUMNS, allowed=MODEL_COLUMNS):
        alias = csvio.text(r["alias"])
        at = csvio.where(path, alias)
        if not alias or alias in models:
            raise csvio.TableError(f"{at}: alias is empty or duplicated")
        spec: dict[str, Any] = {c: csvio.optional(r[c]) for c in MODEL_COLUMNS
                                if c not in ("alias", "timeout_s", "extra_body", *_MODEL_BOOLS)}
        spec.update({c: csvio.boolean(r[c], f"{at} {c}") for c in _MODEL_BOOLS})
        spec["timeout_s"] = csvio.number(r["timeout_s"], f"{at} timeout_s")
        spec["extra_body"] = csvio.json_object(r["extra_body"], f"{at} extra_body")
        try:
            models[alias] = ModelSpec(alias=alias, **spec)
        except ValidationError as e:
            raise csvio.TableError(f"{at}: {e}") from e
    return models


# --------------------------------------------------------------------------- #
# Principle-probe items (A11)
# --------------------------------------------------------------------------- #
class PrincipleItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: str
    keying: Literal["pro", "reverse", "control"]
    item_type: Literal["principle", "control"]
    text: str
    expected_answer: Literal["yes", "no"] | None = None   # control items only

    @model_validator(mode="after")
    def _consistent(self) -> "PrincipleItem":
        if (self.keying == "control") != (self.item_type == "control"):
            raise ValueError(f"{self.item_id}: keying 'control' iff item_type 'control'")
        if self.item_type == "control" and self.expected_answer is None:
            raise ValueError(f"{self.item_id}: control items need expected_answer")
        return self


@dataclass(frozen=True)
class PrincipleSpec:
    generic_context: str
    occupation_context: str
    items: tuple[PrincipleItem, ...]

    def context_text(self, context: str, jobs: dict[str, JobAd]) -> str:
        """The CONTEXT slot value: the generic context, or the occupation context with
        ``{title}`` = the job title of that occupation."""
        if context == "generic":
            return self.generic_context
        return self.occupation_context.replace("{title}", jobs[context].title)

    def by_id(self) -> dict[str, PrincipleItem]:
        return {i.item_id: i for i in self.items}


PRINCIPLE_ITEM_COLUMNS = ("item_id", "keying", "item_type", "expected_answer", "text")


def load_principle_items(path: str | Path, parts_path: str | Path | None = None) -> PrincipleSpec:
    """Read ``prompts/principle_items.csv``; the two probe contexts are the parts
    ``probe_context_generic`` and ``probe_context_occupation`` of
    ``prompts/prompt_parts.csv`` (default: next to the items file)."""
    from .prompts import PROBE_CONTEXT_GENERIC, PROBE_CONTEXT_OCCUPATION, load_parts

    items = []
    for r in csvio.read_rows(path, PRINCIPLE_ITEM_COLUMNS, allowed=PRINCIPLE_ITEM_COLUMNS):
        at = csvio.where(path, csvio.text(r["item_id"]))
        try:
            items.append(PrincipleItem(item_id=csvio.text(r["item_id"]), keying=csvio.text(r["keying"]),
                                       item_type=csvio.text(r["item_type"]),
                                       expected_answer=csvio.optional(r["expected_answer"]),
                                       text=csvio.text(r["text"])))
        except ValidationError as e:
            raise csvio.TableError(f"{at}: {e}") from e
    items = tuple(items)
    ids = [i.item_id for i in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate principle item ids")
    n_pro = sum(i.keying == "pro" for i in items)
    n_rev = sum(i.keying == "reverse" for i in items)
    n_ctrl = sum(i.keying == "control" for i in items)
    if n_pro + n_rev < 10 or n_pro != n_rev or not 2 <= n_ctrl <= 3:
        raise ValueError(f"principle items must be >= 10 statements, half reverse-keyed, plus 2-3 "
                         f"controls (got pro={n_pro}, reverse={n_rev}, control={n_ctrl})")
    parts = load_parts(Path(parts_path) if parts_path else Path(path).parent / "prompt_parts.csv")
    missing = [p for p in (PROBE_CONTEXT_GENERIC, PROBE_CONTEXT_OCCUPATION) if p not in parts]
    if missing:
        raise ValueError(f"prompt_parts.csv lacks the probe context part(s) {missing}")
    return PrincipleSpec(parts[PROBE_CONTEXT_GENERIC].text, parts[PROBE_CONTEXT_OCCUPATION].text, items)


# --------------------------------------------------------------------------- #
# Text flags (exploratory reason-text coding)
# --------------------------------------------------------------------------- #
TEXT_FLAG_FILE_COLUMNS = ("flag", "pattern_type", "pattern", "note")
TEXT_FLAG_PATTERN_TYPES = ("regex", "all_demonyms", "all_country_names", "exclude")


def load_text_flags(path: str | Path) -> dict:
    """Read ``config/text_flags.csv`` into ``{"flags": {flag: {"patterns": [...],
    "include_demonyms": bool, "include_country_names": bool, "exclude": [...]}}}``
    (the structure ``parse_outputs.compile_text_flags`` compiles).

    pattern_type: ``regex`` (a Python regex, case-insensitive, wrapped in word
    boundaries unless it contains ``\\b``); ``all_demonyms`` / ``all_country_names``
    (every demonym / country name of stimuli/nationalities.csv); ``exclude`` (a
    demonym or country name that the two previous types skip).
    """
    flags: dict[str, dict] = {}
    for r in csvio.read_rows(path, TEXT_FLAG_FILE_COLUMNS, allowed=TEXT_FLAG_FILE_COLUMNS):
        flag, ptype, pattern = csvio.text(r["flag"]), csvio.text(r["pattern_type"]), csvio.text(r["pattern"])
        at = csvio.where(path, f"{flag} {pattern}")
        if not flag:
            raise csvio.TableError(f"{at}: empty flag")
        spec = flags.setdefault(flag, {"patterns": [], "include_demonyms": False, "include_country_names": False,
                                       "exclude": []})
        if ptype not in TEXT_FLAG_PATTERN_TYPES:
            raise csvio.TableError(f"{at}: pattern_type must be one of {TEXT_FLAG_PATTERN_TYPES}, got {ptype!r}")
        if (ptype in ("regex", "exclude")) != bool(pattern):
            raise csvio.TableError(f"{at}: pattern_type {ptype} {'needs' if ptype in ('regex', 'exclude') else 'takes no'}"
                                   f" pattern")
        if ptype == "regex":
            spec["patterns"].append(pattern)
        elif ptype == "exclude":
            spec["exclude"].append(pattern)
        else:
            spec["include_" + ptype[len("all_"):]] = True
    return {"flags": flags}



# --------------------------------------------------------------------------- #
# Experiment config
# --------------------------------------------------------------------------- #
class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConditionCfg(_Strict):
    enabled: bool = False
    repetitions: int = Field(default=1, ge=1)


class PrincipleCfg(ConditionCfg):
    contexts: Literal["all"] | list[str] = "all"   # "generic" and/or occupation ids
    items: Literal["all"] | list[str] = "all"      # item ids from prompts/principle_items.csv


class ConditionsCfg(_Strict):
    # Defaults (used only by programmatic configs, e.g. in tests; every run in
    # config/runs.csv sets every value explicitly): design contract v0.2, A3/A9/A11.
    baseline: ConditionCfg = ConditionCfg(enabled=True, repetitions=3)
    neutrality: ConditionCfg = ConditionCfg(enabled=True, repetitions=3)
    forced_choice: ConditionCfg = ConditionCfg(enabled=True, repetitions=1)
    forced_choice_neutrality: ConditionCfg = ConditionCfg(enabled=False, repetitions=1)
    principle_probe: PrincipleCfg = PrincipleCfg(enabled=True, repetitions=5)


class PairDesignCfg(_Strict):
    """Nationality pairs for forced choice (A9).

    The FC nationality levels are decomposed into Hamiltonian cycles (Walecki);
    ``n_cycles`` of them are used (each cycle puts every level in exactly two
    pairs; "all" = every pair) and each selected pair is assigned to ``copies``
    (c) distinct CV pairs.
    """

    n_cycles: int | Literal["all"] = 4
    copies: int = Field(default=1, ge=1)


class ForcedChoiceDesignCfg(_Strict):
    tiers: list[Literal["strong", "adequate", "borderline"]] = Field(default_factory=lambda: list(TIERS))
    exclude_nationalities: list[str] = Field(default_factory=lambda: ["NONE"])
    nationality_pairs: PairDesignCfg = PairDesignCfg()


class SamplingCfg(_Strict):
    temperature: float = 0.7
    top_p: float | None = 1.0
    max_tokens: int = 400
    json_mode: bool = True
    logprobs: bool = True
    top_logprobs: int = 5
    logprobs_max_tokens: int = 40
    # Sent to openai_compatible (vLLM) servers so that model-specific generation
    # defaults cannot silently change decoding (A10: no top_k, identical settings).
    openai_compatible_extra: dict[str, Any] = Field(
        default_factory=lambda: {"top_k": -1, "min_p": 0.0, "repetition_penalty": 1.0})


class ArmCfg(_Strict):
    """A robustness block (A10 greedy decoding)."""

    arm_id: str
    conditions: list[Literal["baseline", "neutrality"]] = Field(default_factory=lambda: ["baseline"])
    repetitions: int = Field(default=1, ge=1)
    temperature: float | None = None           # None = primary temperature
    models: Literal["all"] | list[str] = "all"
    prompt_variants: Literal["all"] | list[str] = "all"

    @field_validator("arm_id")
    @classmethod
    def _not_primary(cls, v: str) -> str:
        if v == "primary" or not v:
            raise ValueError("arm_id must be a non-empty name other than 'primary'")
        return v


class StopRuleCfg(_Strict):
    """Technical stop rule (review M8; prereg section 7), nationality-blind: once a
    model has `first_fraction` of its planned calls answered (api_error excluded,
    review N6), stop it if the share of non-ok answers exceeds `max_non_ok_share`."""

    enabled: bool = True
    first_fraction: float = Field(default=0.05, gt=0.0, le=1.0)
    max_non_ok_share: float = Field(default=0.10, ge=0.0, le=1.0)


class RetryCfg(_Strict):
    max_attempts: int = Field(default=5, ge=1)
    backoff_base_s: float = 2.0
    backoff_max_s: float = 60.0
    max_consecutive_api_errors: int = Field(default=25, ge=1)
    max_api_error_sessions: int = Field(default=3, ge=1)   # N7: api_error-only calls are terminal after this


class PlanCfg(_Strict):
    expected_output_tokens: int = 80


class MockRatesCfg(_Strict):
    malformed_json: float = 0.0
    schema_violation: float = 0.0
    refusal: float = 0.0
    empty: float = 0.0
    api_error_retryable: float = 0.0
    api_error_fatal: float = 0.0
    code_fence: float = 0.0
    leading_prose: float = 0.0


class MockCfg(_Strict):
    """Parameters of the transparent generative model behind MockProvider.

    Every nationality effect here is SYNTHETIC and exists only to test that the
    pipeline and the analysis can recover a known pattern. Default: all zero.
    """

    nationality_effects: dict[str, float] = Field(default_factory=dict)
    effect_pattern: Literal["none", "alphabetical_ramp"] = "none"
    effect_amplitude: float = 0.0
    neutrality_shrink: float = Field(default=0.5, ge=0.0, le=1.0)
    position_bias: float = 0.0
    intercept: float = 50.0
    years_slope: float = 2.5
    qualification_effect: float = 10.0         # fit points lost when the qualification line is missing
    cv_sd: float = 6.0
    noise_sd: float = 5.0
    interview_threshold: float = 60.0
    fc_scale: float = 6.0
    principle_endorse_prob: float = 0.9
    rates: MockRatesCfg = MockRatesCfg()


class ExperimentConfig(_Strict):
    experiment_id: str
    description: str = ""
    run_id: str | None = None
    nationalities: Literal["all"] | list[str] = "all"
    occupations: Literal["all", "pilot"] | list[str] = "all"
    base_cvs: Literal["all", "pilot"] | dict[str, list[str]] = "all"
    models: list[str]
    prompt_variants: list[str] = Field(default_factory=lambda: ["k1", "k2", "k3"])
    positive_control: bool = True              # A7: evaluated under baseline only
    include_placebo: bool = True               # H5: placebo nationalities, baseline IE (primary arm) only
    seed: int = 20261013
    sampling: SamplingCfg = SamplingCfg()
    conditions: ConditionsCfg = ConditionsCfg()
    forced_choice_design: ForcedChoiceDesignCfg = ForcedChoiceDesignCfg()
    robustness_arms: list[ArmCfg] = Field(default_factory=list)
    retry: RetryCfg = RetryCfg()
    stop_rule: StopRuleCfg = StopRuleCfg()
    workers: int = Field(default=1, ge=1)
    plan: PlanCfg = PlanCfg()
    mock: MockCfg = MockCfg()

    @field_validator("experiment_id")
    @classmethod
    def _id_is_path_safe(cls, v: str) -> str:
        if not v or any(ch in v for ch in '/\\:*?"<>| '):
            raise ValueError(f"experiment_id must be a non-empty path-safe string, got {v!r}")
        return v

    @model_validator(mode="after")
    def _checks(self) -> "ExperimentConfig":
        if not any(getattr(self.conditions, c).enabled for c in PROMPT_CONDITIONS):
            raise ValueError("no prompt condition is enabled")
        if not self.prompt_variants or len(set(self.prompt_variants)) != len(self.prompt_variants):
            raise ValueError("prompt_variants must be a non-empty list without duplicates")
        ids = [a.arm_id for a in self.robustness_arms]
        if len(ids) != len(set(ids)):
            raise ValueError("robustness arm ids must be unique")
        return self

    def enabled_conditions(self) -> list[str]:
        return [c for c in PROMPT_CONDITIONS if getattr(self.conditions, c).enabled]

    def repetitions(self, condition: str) -> int:
        return getattr(self.conditions, condition).repetitions

    def hash_payload(self) -> dict:
        """The part of the config that defines the experiment (for config_hash).

        ``workers`` only affects speed and is excluded so a resumed run may use a
        different degree of concurrency.
        """
        d = self.model_dump(mode="json")
        d.pop("workers", None)
        return d

    def config_hash(self) -> str:
        return stable_hash(self.hash_payload())


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge ``override`` into a copy of ``base``.

    Mappings merge key by key; lists and scalars in ``override`` replace.
    """
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def default_config_dict() -> dict:
    """The code defaults of every experiment setting (design contract v0.2), as a dict.

    Used only to complete PROGRAMMATIC configs (dicts, e.g. in tests). The runs in
    config/runs.csv state every setting explicitly and are never merged with these.
    """
    d = ExperimentConfig(experiment_id="defaults", models=["defaults"]).model_dump(mode="json")
    for k in ("experiment_id", "models"):
        d.pop(k)
    return d


def load_experiment_config(source: dict) -> ExperimentConfig:
    """A programmatic config (dict) deep-merged over ``default_config_dict()``."""
    if not isinstance(source, dict):
        raise TypeError("load_experiment_config takes a dict; named runs come from config/runs.csv "
                        "(load_run_config)")
    return ExperimentConfig(**deep_merge(default_config_dict(), dict(source)))


# --------------------------------------------------------------------------- #
# config/runs.csv: one row per run, every setting a column
# --------------------------------------------------------------------------- #
RUN_CONDITIONS = ("baseline", "neutrality", "forced_choice", "forced_choice_neutrality", "principle_probe")
_SAMPLING = (("temperature", "float"), ("top_p", "float?"), ("max_tokens", "int"), ("json_mode", "bool"),
             ("logprobs", "bool"), ("top_logprobs", "int"), ("logprobs_max_tokens", "int"),
             ("openai_compatible_extra", "json"))
_STOP = (("enabled", "bool"), ("first_fraction", "float"), ("max_non_ok_share", "float"))
_RETRY = (("max_attempts", "int"), ("backoff_base_s", "float"), ("backoff_max_s", "float"),
          ("max_consecutive_api_errors", "int"), ("max_api_error_sessions", "int"))
_MOCK = (("effect_pattern", "str"), ("effect_amplitude", "float"), ("neutrality_shrink", "float"),
         ("position_bias", "float"), ("intercept", "float"), ("years_slope", "float"),
         ("qualification_effect", "float"), ("cv_sd", "float"), ("noise_sd", "float"),
         ("interview_threshold", "float"), ("fc_scale", "float"), ("principle_endorse_prob", "float"))
_MOCK_RATES = ("malformed_json", "schema_violation", "refusal", "empty", "api_error_retryable", "api_error_fatal",
               "code_fence", "leading_prose")
_GREEDY = ("greedy_conditions", "greedy_temperature", "greedy_repetitions", "greedy_models",
           "greedy_prompt_variants")
RUN_COLUMNS = (
    "run", "experiment_id", "run_id", "description", "models", "occupations", "base_cvs", "nationalities",
    "include_placebo", "positive_control", "prompt_variants", "seed",
    *[f"{c}_{x}" for c in RUN_CONDITIONS for x in ("enabled", "repetitions")],
    "principle_probe_contexts", "principle_probe_items",
    "fc_tiers", "fc_exclude_nationalities", "fc_n_cycles", "fc_copies",
    "greedy_arm", *_GREEDY,
    *[k for k, _ in _SAMPLING],
    *[f"stop_rule_{k}" for k, _ in _STOP], *[f"retry_{k}" for k, _ in _RETRY],
    "workers", "plan_expected_output_tokens",
    *[f"mock_{k}" for k, _ in _MOCK], *[f"mock_rate_{k}" for k in _MOCK_RATES],
)
OPTIONAL_RUN_COLUMNS = ("run_id", "description")


class RunConfigError(ValueError):
    """config/runs.csv cannot be read, or a run name is unknown."""


def _cell(row: dict, col: str, kind: str, at: str):
    raw = row[col]
    optional = kind.endswith("?") or col in OPTIONAL_RUN_COLUMNS
    kind = kind.rstrip("?")
    if not csvio.text(raw):
        if optional:
            return "" if kind == "str" else None
        raise csvio.TableError(f"{at}: column {col!r} is empty (every setting is given explicitly)")
    a = f"{at} {col}"
    if kind == "str":
        return csvio.text(raw)
    if kind == "int":
        return csvio.integer(raw, a)
    if kind == "float":
        return csvio.number(raw, a)
    if kind == "bool":
        return csvio.boolean(raw, a)
    if kind == "list":
        return csvio.items(raw)
    if kind == "json":
        return csvio.json_object(raw, a)
    if kind.startswith("kw:"):
        return csvio.keyword_or_items(raw, tuple(kind[3:].split(",")), a)
    raise AssertionError(kind)


def _base_cvs(raw: str, at: str):
    v = csvio.text(raw)
    if not v:
        raise csvio.TableError(f"{at}: column 'base_cvs' is empty")
    if v in ("all", "pilot"):
        return v
    out: dict[str, list[str]] = {}
    for item in csvio.items(v):
        occ, sep, cv = item.partition(":")
        if not sep or not occ.strip() or not cv.strip():
            raise csvio.TableError(f"{at} base_cvs: expected all, pilot or 'occupation:cv_id | ...', got {item!r}")
        out.setdefault(occ.strip(), []).append(cv.strip())
    return out


def run_row_to_config(row: dict, at: str) -> dict:
    """One row of config/runs.csv -> the nested config dict of ExperimentConfig."""
    def c(col: str, kind: str):
        return _cell(row, col, kind, at)

    fc_cycles = c("fc_n_cycles", "str")
    d: dict[str, Any] = {
        "experiment_id": c("experiment_id", "str"),
        "run_id": c("run_id", "str") or None,
        "description": c("description", "str"),
        "models": c("models", "list"),
        "occupations": c("occupations", "kw:all,pilot"),
        "base_cvs": _base_cvs(row["base_cvs"], at),
        "nationalities": c("nationalities", "kw:all"),
        "include_placebo": c("include_placebo", "bool"),
        "positive_control": c("positive_control", "bool"),
        "prompt_variants": c("prompt_variants", "list"),
        "seed": c("seed", "int"),
        "conditions": {cond: {"enabled": c(f"{cond}_enabled", "bool"),
                              "repetitions": c(f"{cond}_repetitions", "int")} for cond in RUN_CONDITIONS},
        "forced_choice_design": {
            "tiers": c("fc_tiers", "list"), "exclude_nationalities": c("fc_exclude_nationalities", "list"),
            "nationality_pairs": {"n_cycles": fc_cycles if fc_cycles == "all"
                                  else csvio.integer(fc_cycles, f"{at} fc_n_cycles"),
                                  "copies": c("fc_copies", "int")}},
        "sampling": {k: c(k, kind) for k, kind in _SAMPLING},
        "stop_rule": {k: c(f"stop_rule_{k}", kind) for k, kind in _STOP},
        "retry": {k: c(f"retry_{k}", kind) for k, kind in _RETRY},
        "workers": c("workers", "int"),
        "plan": {"expected_output_tokens": c("plan_expected_output_tokens", "int")},
        "mock": {**{k: c(f"mock_{k}", kind) for k, kind in _MOCK},
                 "rates": {k: c(f"mock_rate_{k}", "float") for k in _MOCK_RATES}},
        "robustness_arms": [],
    }
    d["conditions"]["principle_probe"]["contexts"] = c("principle_probe_contexts", "kw:all")
    d["conditions"]["principle_probe"]["items"] = c("principle_probe_items", "kw:all")
    if c("greedy_arm", "bool"):
        d["robustness_arms"] = [{"arm_id": "greedy", "conditions": c("greedy_conditions", "list"),
                                 "temperature": c("greedy_temperature", "float"),
                                 "repetitions": c("greedy_repetitions", "int"),
                                 "models": c("greedy_models", "kw:all"),
                                 "prompt_variants": c("greedy_prompt_variants", "kw:all")}]
    else:
        filled = [g for g in _GREEDY if csvio.text(row[g])]
        if filled:
            raise csvio.TableError(f"{at}: greedy_arm is false but {filled} are filled in")
    return d


def run_names(path: str | Path) -> list[str]:
    return [csvio.text(r["run"]) for r in csvio.read_rows(path, ("run",))]


def load_run_config(path: str | Path, run: str) -> ExperimentConfig:
    """The ExperimentConfig of row ``run`` of config/runs.csv. Nothing is merged:
    every setting is a column of that row."""
    rows = csvio.read_rows(path, RUN_COLUMNS, allowed=RUN_COLUMNS)
    names = [csvio.text(r["run"]) for r in rows]
    if len(names) != len(set(names)):
        raise RunConfigError(f"{path}: duplicate run names {sorted({n for n in names if names.count(n) > 1})}")
    if run not in names:
        raise RunConfigError(f"unknown run {run!r}; config/runs.csv defines {names}")
    at = csvio.where(path, run)
    try:
        return ExperimentConfig(**run_row_to_config(rows[names.index(run)], at))
    except ValidationError as e:
        raise RunConfigError(f"{at}: {e}") from e
