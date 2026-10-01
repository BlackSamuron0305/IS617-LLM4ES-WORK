"""Output JSON schemas (contract section 4, A11) and record/table field lists (sections 6-7, A18)."""

from __future__ import annotations

_SCORE = {"type": "integer", "minimum": 0, "maximum": 100}

INDEPENDENT_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_fit": _SCORE,
        "interview": {"enum": ["yes", "no"]},
        "confidence": _SCORE,
        "reason": {"type": "string"},
    },
    "required": ["overall_fit", "interview", "confidence", "reason"],
    "additionalProperties": False,
}

FORCED_CHOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "choice": {"enum": ["A", "B"]},
        "confidence": _SCORE,
        "reason": {"type": "string"},
    },
    "required": ["choice", "confidence", "reason"],
    "additionalProperties": False,
}

# A11: replaces the v0.1 {"endorses_neutrality", ...} schema
PRINCIPLE_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"enum": ["yes", "no"]},
        "agreement": _SCORE,
        "reason": {"type": "string"},
    },
    "required": ["answer", "agreement", "reason"],
    "additionalProperties": False,
}

SCHEMA_BY_TASK = {
    "independent": INDEPENDENT_SCHEMA,
    "forced_choice": FORCED_CHOICE_SCHEMA,
    "principle_probe": PRINCIPLE_SCHEMA,
}

PARSE_STATUSES = ("ok", "malformed_json", "schema_violation", "refusal", "empty", "api_error")

# Contract section 6 + A18: required fields of every raw call record.
RAW_RECORD_FIELDS = (
    "record_id", "trial_id", "run_id", "experiment_id", "config_hash", "timestamp_utc",
    "provider", "model_id", "model_alias", "temperature", "top_p", "max_tokens", "seed",
    "system_prompt_version", "user_prompt_version", "prompt_condition", "task_type",
    "occupation", "repetition", "stimulus_ids", "base_cv_ids", "nationalities",
    "qualification_tier", "fc_order", "quad_id", "prompt_sha256", "raw_output",
    "finish_reason", "usage", "latency_ms", "logprobs", "parsed", "parse_status",
    "refusal", "api_error", "attempts", "is_mock",
    # A18
    "prompt_variant", "execution_index", "model_revision", "clone_type",
    # setting (user request 2026-10-01): base country of the CV(s); host_national is
    # aligned with `nationalities` (nationality code == base country), null for probes
    "base_country", "host_national",
)

TEXT_FLAG_COLUMNS = (
    "mentions_nationality", "mentions_language", "mentions_visa",
    "mentions_culture_fit", "mentions_religion", "mentions_conflict",
    "mentions_testing",  # A18: evaluation awareness
)

# Contract section 7 columns first (same order), then v0.2 additions.
EVALUATION_COLUMNS = (
    "run_id", "record_id", "trial_id", "is_mock", "provider", "model_id", "model_alias",
    "prompt_condition", "occupation", "base_cv_id", "qualification_tier", "nationality",
    "nationality_group", "subregion", "arab_identity_contested", "repetition", "overall_fit",
    "interview", "confidence", "reason", "parse_status", "refusal", "api_error",
) + TEXT_FLAG_COLUMNS + (
    "pronoun_gender",                                   # A18: he|she|they|none
    "prompt_variant", "clone_type", "execution_index", "seed", "model_revision",   # A18
    "arm", "temperature",                               # robustness arm (A10 greedy decoding)
) + ("prompt_sha256", "user_prompt_version", "n_json_objects", "near_miss") + (   # review H3, L4
    "base_country", "host_national",                    # setting (2026-10-01): nationality == base country
)

FORCED_CHOICE_COLUMNS = (
    "run_id", "record_id", "trial_id", "quad_id", "is_mock", "provider", "model_id",
    "model_alias", "prompt_condition", "occupation", "qualification_tier", "cv_a", "cv_b",
    "nationality_a", "nationality_b", "fc_order", "choice", "chosen_nationality", "chosen_cv",
    "confidence", "reason", "parse_status", "refusal", "api_error",
    "prompt_variant", "execution_index", "seed", "model_revision", "repetition",
    "prompt_sha256", "user_prompt_version", "n_json_objects", "near_miss",
    "base_country", "host_national_a", "host_national_b",   # setting (2026-10-01): one base country per pair
)

PRINCIPLE_COLUMNS = (
    "run_id", "record_id", "is_mock", "provider", "model_id", "model_alias", "probe_id",
    "occupation", "repetition", "endorses_neutrality", "agreement", "reason", "parse_status",
    "refusal", "api_error",
    "item_id", "keying", "item_type", "context", "answer",             # A11
    "expected_answer",                                                 # control items only
    "prompt_variant", "execution_index", "seed", "model_revision",     # A18 (no wording variants: NA)
    "prompt_sha256", "user_prompt_version", "n_json_objects", "near_miss",
)
