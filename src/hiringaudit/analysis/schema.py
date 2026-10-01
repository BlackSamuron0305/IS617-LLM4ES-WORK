"""Loading and validation of the processed tables (design contract v0.2, section 7 + A3/A7/A9/A11/A18).

Every loader fails loudly: all detected problems are collected and raised
together as a :class:`SchemaError`. Nothing is coerced silently; values that
cannot be mapped to the contract are reported, never guessed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

MOCK_BANNER = "SYNTHETIC MOCK DATA — NOT RESULTS"
ARAB_LABEL = "Arab League member-state nationalities"   # A19

REFERENCE = "DEU"
CONTROL = "NONE"

PARSE_STATUSES = frozenset(
    {"ok", "malformed_json", "schema_violation", "refusal", "empty", "api_error"}
)
NATIONALITY_GROUPS = frozenset({"arab", "benchmark", "control", "placebo"})
PLACEBO = "placebo"
# Mirror of the placebo rows in stimuli/nationalities.csv (a test checks they agree).
PLACEBO_CODES = ("URY", "BOL", "SYC", "MWI", "MDV", "NPL", "MYS", "KHM")
EVAL_CONDITIONS = frozenset({"baseline", "neutrality"})
FC_CONDITIONS = frozenset({"forced_choice", "forced_choice_neutrality"})
CLONE_TYPES = frozenset({"counterfactual", "positive_control"})
KEYINGS = frozenset({"pro", "reverse", "control"})
ITEM_TYPES = frozenset({"principle", "control"})
PRONOUNS = frozenset({"he", "she", "they", "none"})
TEXT_FLAGS = (
    "mentions_nationality",
    "mentions_language",
    "mentions_visa",
    "mentions_culture_fit",
    "mentions_religion",
    "mentions_conflict",
    "mentions_testing",
)

EVALUATION_COLUMNS = (
    "run_id", "record_id", "trial_id", "is_mock", "provider", "model_id",
    "model_alias", "model_revision", "prompt_condition", "prompt_variant", "clone_type",
    "occupation", "base_cv_id", "qualification_tier", "nationality", "nationality_group",
    "subregion", "arab_identity_contested", "repetition", "execution_index", "seed",
    "overall_fit", "interview", "confidence", "reason", "parse_status", "refusal",
    "api_error", "pronoun_gender",
) + TEXT_FLAGS + (
    # setting (2026-10-01): every base CV is set in one Arab League base country; host_national is
    # True iff the clone's nationality code equals the CV's base country (validated below)
    "base_country", "host_national",
)

# Optional evaluation columns (engineer output): ``arm`` (primary | robustness arms such as
# greedy), ``temperature``. When ``arm`` is absent every row is treated as the primary arm. Confirmatory analyses use arm == "primary" only.
PRIMARY_ARM = "primary"

FORCED_CHOICE_COLUMNS = (
    "run_id", "record_id", "trial_id", "quad_id", "is_mock", "provider",
    "model_id", "model_alias", "prompt_condition", "prompt_variant", "occupation",
    "qualification_tier", "cv_a", "cv_b", "nationality_a", "nationality_b",
    "fc_order", "choice", "chosen_nationality", "chosen_cv", "confidence",
    "reason", "parse_status", "refusal", "api_error",
    # setting (2026-10-01): the two CVs of a forced-choice pair share one base country
    "base_country", "host_national_a", "host_national_b",
)

PRINCIPLE_COLUMNS = (
    "run_id", "record_id", "is_mock", "provider", "model_id", "model_alias",
    "item_id", "keying", "item_type", "context", "repetition", "answer",
    "endorses_neutrality", "agreement", "reason", "parse_status", "refusal", "api_error",
)
# Optional principle column used for the control-item check when present:
# ``expected_answer`` (yes|no on control items, NA otherwise).

_NA_TOKENS = ["", "NA", "N/A", "NaN", "nan", "null", "NULL", "<NA>"]
_TRUE = {"true", "1", "yes", "t", "y"}
_FALSE = {"false", "0", "no", "f", "n"}


class SchemaError(ValueError):
    """Raised when a processed table does not match the design contract."""

    def __init__(self, table: str, problems: list[str]):
        self.table = table
        self.problems = list(problems)
        msg = f"{table}: {len(problems)} schema problem(s):\n  - " + "\n  - ".join(problems)
        super().__init__(msg)


# --------------------------------------------------------------------------- #
# Coercion helpers (they record problems rather than guessing)
# --------------------------------------------------------------------------- #
def _to_bool(s: pd.Series, name: str, problems: list[str], allow_na: bool) -> pd.Series:
    def conv(v):
        if v is None or v is pd.NA or (isinstance(v, float) and np.isnan(v)):
            return pd.NA
        if isinstance(v, (bool, np.bool_)):
            return bool(v)
        if isinstance(v, (int, np.integer)) and v in (0, 1):
            return bool(v)
        if isinstance(v, (float, np.floating)) and v in (0.0, 1.0):
            return bool(v)
        t = str(v).strip().lower()
        if t in _TRUE:
            return True
        if t in _FALSE:
            return False
        return "__bad__"

    out = s.map(conv)
    bad = out.map(lambda v: isinstance(v, str))
    if bad.any():
        ex = s[bad].astype(str).unique()[:5].tolist()
        problems.append(f"column '{name}' has non-boolean values, e.g. {ex}")
        out = out.where(~bad, pd.NA)
    if not allow_na and out.isna().any():
        problems.append(f"column '{name}' has {int(out.isna().sum())} missing value(s)")
    return out.astype("boolean")


def _truthy_error(s: pd.Series) -> pd.Series:
    """``api_error`` may be a boolean or an error message; True when an error is recorded."""
    t = s.astype("string").str.strip().str.lower()
    return (s.notna() & ~t.isin(["", "false", "0", "none", "nan"])).fillna(False).astype(bool)


def _to_num(s: pd.Series, name: str, problems: list[str]) -> pd.Series:
    out = pd.to_numeric(s, errors="coerce")
    bad = out.isna() & s.notna()
    if bad.any():
        ex = s[bad].astype(str).unique()[:5].tolist()
        problems.append(f"column '{name}' has non-numeric values, e.g. {ex}")
    return out.astype(float)


def _check_range(s: pd.Series, name: str, lo: float, hi: float, problems: list[str]) -> None:
    bad = s.notna() & ((s < lo) | (s > hi))
    if bad.any():
        problems.append(f"column '{name}' has {int(bad.sum())} value(s) outside [{lo}, {hi}]")


def _check_allowed(s: pd.Series, name: str, allowed, problems: list[str], allow_na=False) -> None:
    vals = s.dropna() if allow_na else s
    bad = ~vals.isin(list(allowed)).fillna(False)
    if bad.any():
        ex = vals[bad].astype(str).unique()[:8].tolist()
        problems.append(f"column '{name}' has values outside {sorted(allowed)}: {ex}")


def _check_required(df: pd.DataFrame, cols, problems: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        problems.append(f"missing required column(s): {missing}")


def _check_nonnull(df: pd.DataFrame, cols, problems: list[str]) -> None:
    for c in cols:
        if c in df.columns and df[c].isna().any():
            problems.append(f"column '{c}' has {int(df[c].isna().sum())} missing value(s)")


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, na_values=_NA_TOKENS, low_memory=False)


def _string_cols(df: pd.DataFrame, cols) -> None:
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype("string").str.strip()


def _eq(s: pd.Series, v) -> pd.Series:
    return (s == v).fillna(False).astype(bool)


# --------------------------------------------------------------------------- #
# evaluations.csv
# --------------------------------------------------------------------------- #
def validate_evaluations(df: pd.DataFrame, table: str = "evaluations.csv") -> pd.DataFrame:
    """Validate and type an evaluations table. Returns a typed copy."""
    problems: list[str] = []
    df = df.copy()
    _check_required(df, EVALUATION_COLUMNS, problems)
    if problems:
        raise SchemaError(table, problems)
    if len(df) == 0:
        raise SchemaError(table, ["table has no rows"])

    if "arm" not in df.columns:
        df["arm"] = PRIMARY_ARM
    _string_cols(df, ["run_id", "record_id", "trial_id", "provider", "model_id", "model_alias",
                      "model_revision", "prompt_condition", "prompt_variant", "clone_type",
                      "occupation", "base_cv_id", "qualification_tier", "nationality",
                      "nationality_group", "subregion", "parse_status", "pronoun_gender", "arm",
                      "base_country"])
    _check_nonnull(df, ["arm"], problems)
    if "temperature" in df.columns:
        df["temperature"] = _to_num(df["temperature"], "temperature", problems)
    _check_nonnull(df, ["record_id", "model_alias", "model_id", "prompt_condition", "prompt_variant",
                        "clone_type", "occupation", "base_cv_id", "qualification_tier",
                        "nationality", "nationality_group", "parse_status", "repetition"], problems)

    df["is_mock"] = _to_bool(df["is_mock"], "is_mock", problems, allow_na=False)
    df["refusal"] = _to_bool(df["refusal"], "refusal", problems, allow_na=True)
    df["api_error_flag"] = _truthy_error(df["api_error"])
    df["arab_identity_contested"] = _to_bool(
        df["arab_identity_contested"], "arab_identity_contested", problems, allow_na=False)
    df["host_national"] = _to_bool(df["host_national"], "host_national", problems, allow_na=False)
    _check_nonnull(df, ["base_country"], problems)
    for f in TEXT_FLAGS:
        df[f] = _to_bool(df[f], f, problems, allow_na=True)

    for c in ("repetition", "execution_index", "seed", "overall_fit", "interview", "confidence"):
        df[c] = _to_num(df[c], c, problems)
    _check_range(df["overall_fit"], "overall_fit", 0, 100, problems)
    _check_range(df["confidence"], "confidence", 0, 100, problems)
    _check_allowed(df["interview"], "interview", {0.0, 1.0}, problems, allow_na=True)
    if (df["repetition"].dropna() < 0).any():
        problems.append("column 'repetition' has negative values")

    _check_allowed(df["parse_status"], "parse_status", PARSE_STATUSES, problems)
    _check_allowed(df["nationality_group"], "nationality_group", NATIONALITY_GROUPS, problems)
    _check_allowed(df["prompt_condition"], "prompt_condition", EVAL_CONDITIONS, problems)
    _check_allowed(df["clone_type"], "clone_type", CLONE_TYPES, problems)
    _check_allowed(df["pronoun_gender"], "pronoun_gender", PRONOUNS, problems, allow_na=True)

    ok = _eq(df["parse_status"], "ok")
    for col in ("overall_fit", "interview"):
        n_bad = int((ok & df[col].isna()).sum())
        if n_bad:
            problems.append(f"{n_bad} row(s) have parse_status == 'ok' but missing '{col}' "
                            "(a schema-valid response must carry both primary outcomes)")
    pc = _eq(df["clone_type"], "positive_control")
    if (pc & ~_eq(df["nationality"], CONTROL)).any():
        problems.append("positive_control rows must have nationality == 'NONE' (A7)")
    if (pc & ~_eq(df["prompt_condition"], "baseline")).any():
        problems.append("positive_control rows must be under prompt_condition == 'baseline' (A7)")

    if df["record_id"].duplicated().any():
        problems.append(f"{int(df['record_id'].duplicated().sum())} duplicated record_id value(s)")
    key = ["arm", "model_alias", "prompt_condition", "prompt_variant", "clone_type",
           "base_cv_id", "nationality", "repetition"]
    dk = df.duplicated(key)
    if dk.any():
        problems.append(f"{int(dk.sum())} duplicated (arm, model, condition, variant, clone_type, "
                        "cv, nationality, repetition) cell(s)")
    cf = df[~pc & _eq(df["arm"], PRIMARY_ARM)]
    for meta in ("nationality_group", "subregion", "arab_identity_contested"):
        n_meta = cf.groupby("nationality", observed=True)[meta].nunique(dropna=False)
        if (n_meta > 1).any():
            problems.append(f"nationality codes with inconsistent '{meta}': "
                            f"{n_meta[n_meta > 1].index.tolist()}")
    _check_host_status(df, "nationality", "host_national", problems)
    grp = df[["nationality", "nationality_group"]].dropna().drop_duplicates().set_index("nationality")
    non_arab = set(grp.index[grp["nationality_group"] != "arab"])
    bad_bc = sorted(set(df["base_country"].dropna()) & non_arab)
    if bad_bc:
        problems.append(f"base_country values that are not Arab League nationality codes: {bad_bc} "
                        "(every base country is an Arab League member state)")
    for meta in ("occupation", "qualification_tier", "base_country"):
        n_meta = df.groupby("base_cv_id", observed=True)[meta].nunique(dropna=False)
        if (n_meta > 1).any():
            problems.append(f"base CVs with inconsistent '{meta}': "
                            f"{n_meta[n_meta > 1].index.tolist()[:5]}")
    n_mid = df.groupby("model_alias", observed=True)["model_id"].nunique()
    if (n_mid > 1).any():
        problems.append(f"model_alias mapped to several model_id values: {n_mid[n_mid > 1].index.tolist()}")
    plc = _eq(df["nationality_group"], PLACEBO)
    if (plc & ~(_eq(df["prompt_condition"], "baseline") & _eq(df["arm"], PRIMARY_ARM)
                & _eq(df["clone_type"], "counterfactual"))).any():
        problems.append("placebo nationalities may only appear as counterfactual clones under baseline in the "
                        "primary arm")
    _check_provenance(df, "evaluations", problems,
                      stim_keys=["arm", "model_alias", "prompt_condition", "prompt_variant",
                                 "clone_type", "base_cv_id", "nationality"])
    if cf.empty:
        problems.append(f"no counterfactual rows in arm '{PRIMARY_ARM}'")
    if REFERENCE not in set(cf["nationality"].dropna()):
        problems.append(f"reference nationality '{REFERENCE}' is absent among primary-arm counterfactual clones")
    if "arab" not in set(cf["nationality_group"].dropna()):
        problems.append("no primary-arm counterfactual rows with nationality_group == 'arab'")

    if problems:
        raise SchemaError(table, problems)
    df["repetition"] = df["repetition"].astype(int)
    return df


def _check_host_status(df: pd.DataFrame, nat_col: str, host_col: str, problems: list[str]) -> None:
    """host_national must equal (nationality code == base_country) on every row (setting 2026-10-01)."""
    if host_col not in df.columns or "base_country" not in df.columns:
        return
    expected = (df[nat_col].astype("string") == df["base_country"].astype("string")).fillna(False).astype(bool)
    got = df[host_col]
    bad = got.notna().to_numpy(bool) & (got.fillna(False).astype(bool).to_numpy() != expected.to_numpy())
    if bad.any():
        ex = df.loc[bad, [nat_col, "base_country", host_col]].astype(str).drop_duplicates().head(3)
        problems.append(f"{int(bad.sum())} row(s) where '{host_col}' != ({nat_col} == base_country), e.g. "
                        f"{ex.to_dict(orient='records')}")


# --------------------------------------------------------------------------- #
# forced_choice.csv
# --------------------------------------------------------------------------- #
def _check_provenance(df: pd.DataFrame, table: str, problems: list[str], stim_keys: list[str] | None) -> None:
    """Review H3: one model revision per alias; one user prompt version per (alias, condition, variant);
    one rendered prompt per stimulus. Checks run only when the columns exist."""
    if "model_revision" in df.columns:
        r = df.groupby("model_alias", observed=True)["model_revision"].nunique(dropna=True)
        if (r > 1).any():
            problems.append(f"{table}: model_alias with more than one model_revision (mixed run): "
                            f"{r[r > 1].index.tolist()}")
    if "user_prompt_version" in df.columns and {"prompt_condition", "prompt_variant"} <= set(df.columns):
        v = df.groupby(["model_alias", "prompt_condition", "prompt_variant"], observed=True,
                       dropna=False)["user_prompt_version"].nunique(dropna=True)
        if (v > 1).any():
            problems.append(f"{table}: more than one user_prompt_version within (model, condition, variant): "
                            f"{[tuple(map(str, k)) for k in v[v > 1].index.tolist()][:5]}")
    if stim_keys and "prompt_sha256" in df.columns:
        ok = df["prompt_sha256"].notna()
        if ok.any():
            n = df[ok].groupby(stim_keys, observed=True, dropna=False)["prompt_sha256"].nunique()
            if (n > 1).any():
                problems.append(f"{table}: {int((n > 1).sum())} stimulus cell(s) rendered with more than one "
                                "prompt (prompt_sha256 differs between replicates: mixed run)")


def validate_forced_choice(df: pd.DataFrame, table: str = "forced_choice.csv") -> pd.DataFrame:
    problems: list[str] = []
    df = df.copy()
    _check_required(df, FORCED_CHOICE_COLUMNS, problems)
    if problems:
        raise SchemaError(table, problems)
    _string_cols(df, ["run_id", "record_id", "trial_id", "quad_id", "provider", "model_id",
                      "model_alias", "prompt_condition", "prompt_variant", "occupation",
                      "qualification_tier", "cv_a", "cv_b", "nationality_a", "nationality_b",
                      "fc_order", "choice", "chosen_nationality", "chosen_cv", "parse_status",
                      "base_country"])
    _check_nonnull(df, ["record_id", "trial_id", "quad_id", "model_alias", "prompt_condition",
                        "prompt_variant", "occupation", "cv_a", "cv_b", "nationality_a",
                        "nationality_b", "parse_status", "base_country"], problems)
    for c in ("host_national_a", "host_national_b"):
        df[c] = _to_bool(df[c], c, problems, allow_na=False)
    _check_host_status(df, "nationality_a", "host_national_a", problems)
    _check_host_status(df, "nationality_b", "host_national_b", problems)
    nb = df.groupby("quad_id", observed=True)["base_country"].nunique()
    if (nb > 1).any():
        problems.append(f"{int((nb > 1).sum())} quad(s) with more than one base_country (an FC pair shares one)")
    df["is_mock"] = _to_bool(df["is_mock"], "is_mock", problems, allow_na=False)
    df["refusal"] = _to_bool(df["refusal"], "refusal", problems, allow_na=True)
    df["api_error_flag"] = _truthy_error(df["api_error"])
    df["confidence"] = _to_num(df["confidence"], "confidence", problems)
    if "repetition" in df.columns:
        df["repetition"] = _to_num(df["repetition"], "repetition", problems)
    _check_range(df["confidence"], "confidence", 0, 100, problems)
    _check_allowed(df["parse_status"], "parse_status", PARSE_STATUSES, problems)
    _check_allowed(df["prompt_condition"], "prompt_condition", FC_CONDITIONS, problems)
    _check_allowed(df["choice"], "choice", {"A", "B"}, problems, allow_na=True)

    if (df["cv_a"] == df["cv_b"]).fillna(False).any():
        problems.append(f"{int((df['cv_a'] == df['cv_b']).fillna(False).sum())} row(s) pair a CV with itself")
    if (df["nationality_a"] == df["nationality_b"]).fillna(False).any():
        problems.append("row(s) pair a nationality with itself")
    if (_eq(df["nationality_a"], CONTROL) | _eq(df["nationality_b"], CONTROL)).any():
        problems.append("nationality 'NONE' appears in forced choice (excluded by A9)")
    ok = _eq(df["parse_status"], "ok")
    if (ok & df["choice"].isna()).any():
        problems.append(f"{int((ok & df['choice'].isna()).sum())} row(s) have parse_status 'ok' but no choice")
    has = df["choice"].isin(["A", "B"]).fillna(False).to_numpy(bool)
    is_a = _eq(df["choice"], "A").to_numpy(bool)

    def _obj(col):
        return df[col].astype(object).where(df[col].notna(), None).to_numpy()

    exp_nat = np.where(is_a, _obj("nationality_a"), _obj("nationality_b"))
    exp_cv = np.where(is_a, _obj("cv_a"), _obj("cv_b"))
    if (has & (_obj("chosen_nationality") != exp_nat)).any():
        problems.append("row(s) where chosen_nationality does not match choice")
    if (has & (_obj("chosen_cv") != exp_cv)).any():
        problems.append("row(s) where chosen_cv does not match choice")
    if df["record_id"].duplicated().any():
        problems.append(f"{int(df['record_id'].duplicated().sum())} duplicated record_id value(s)")
    nv = df.groupby("quad_id", observed=True)["prompt_variant"].nunique()
    if (nv > 1).any():
        problems.append(f"{int((nv > 1).sum())} quad(s) mix prompt variants (A3: one variant per quad)")
    if (df["nationality_a"].isin(PLACEBO_CODES) | df["nationality_b"].isin(PLACEBO_CODES)).fillna(False).any():
        problems.append("placebo nationalities appear in forced choice (baseline independent evaluation only)")
    _check_provenance(df, "forced_choice", problems,
                      stim_keys=["model_alias", "prompt_condition", "prompt_variant", "quad_id", "cv_a", "cv_b",
                                 "nationality_a", "nationality_b"])
    if problems:
        raise SchemaError(table, problems)
    return df


# --------------------------------------------------------------------------- #
# principle.csv
# --------------------------------------------------------------------------- #
def validate_principle(df: pd.DataFrame, table: str = "principle.csv") -> pd.DataFrame:
    problems: list[str] = []
    df = df.copy()
    _check_required(df, PRINCIPLE_COLUMNS, problems)
    if problems:
        raise SchemaError(table, problems)
    _string_cols(df, ["run_id", "record_id", "provider", "model_id", "model_alias", "item_id",
                      "keying", "item_type", "context", "answer", "endorses_neutrality",
                      "parse_status", "expected_answer"])
    _check_nonnull(df, ["record_id", "model_alias", "item_id", "keying", "item_type", "context",
                        "parse_status"], problems)
    df["is_mock"] = _to_bool(df["is_mock"], "is_mock", problems, allow_na=False)
    df["refusal"] = _to_bool(df["refusal"], "refusal", problems, allow_na=True)
    df["api_error_flag"] = _truthy_error(df["api_error"])
    df["agreement"] = _to_num(df["agreement"], "agreement", problems)
    df["repetition"] = _to_num(df["repetition"], "repetition", problems)
    _check_range(df["agreement"], "agreement", 0, 100, problems)
    _check_allowed(df["parse_status"], "parse_status", PARSE_STATUSES, problems)
    _check_allowed(df["keying"], "keying", KEYINGS, problems)
    _check_allowed(df["item_type"], "item_type", ITEM_TYPES, problems)
    _check_allowed(df["answer"], "answer", {"yes", "no"}, problems, allow_na=True)
    _check_allowed(df["endorses_neutrality"], "endorses_neutrality", {"yes", "no"}, problems, allow_na=True)
    if "expected_answer" in df.columns:
        _check_allowed(df["expected_answer"], "expected_answer", {"yes", "no"}, problems, allow_na=True)
    ctrl = _eq(df["item_type"], "control")
    if (ctrl != _eq(df["keying"], "control")).any():
        problems.append("item_type == 'control' must coincide with keying == 'control'")
    if (ctrl & df["endorses_neutrality"].notna()).any():
        problems.append("control items must have endorses_neutrality = NA (A11)")
    ok = _eq(df["parse_status"], "ok")
    if (ok & df["answer"].isna()).any():
        problems.append("rows with parse_status 'ok' but missing answer")
    # derived endorsement must equal answer x keying
    ans = df["answer"].astype(object).where(df["answer"].notna(), "__NA__")
    exp = pd.Series("__NA__", index=df.index, dtype=object)
    pro, rev = _eq(df["keying"], "pro"), _eq(df["keying"], "reverse")
    exp[pro] = ans[pro]
    exp[rev] = ans[rev].map({"yes": "no", "no": "yes", "__NA__": "__NA__"})
    got = df["endorses_neutrality"].astype(object).where(df["endorses_neutrality"].notna(), "__NA__")
    tgt = (ok & ~ctrl & df["answer"].notna()).to_numpy(bool)
    mismatch = tgt & (got.to_numpy() != exp.to_numpy())
    if mismatch.any():
        problems.append(f"{int(mismatch.sum())} row(s) where endorses_neutrality != answer x keying")
    if df["record_id"].duplicated().any():
        problems.append(f"{int(df['record_id'].duplicated().sum())} duplicated record_id value(s)")
    _check_provenance(df, "principle", problems, stim_keys=None)
    if problems:
        raise SchemaError(table, problems)
    return df


# --------------------------------------------------------------------------- #
# Directory loader
# --------------------------------------------------------------------------- #
def load_processed(processed_dir: str | Path) -> dict[str, pd.DataFrame | None]:
    """Load and validate the processed tables in ``processed_dir``.

    ``evaluations.csv`` is required and must have rows. ``forced_choice.csv``
    and ``principle.csv`` are optional: absent or header-only files give
    ``None``; files with rows are validated. Raises :class:`SchemaError` on any
    contract violation and ``FileNotFoundError`` if the directory or the
    evaluations table is missing.
    """
    d = Path(processed_dir)
    if not d.is_dir():
        raise FileNotFoundError(f"processed directory not found: {d}")
    ev_path = d / "evaluations.csv"
    if not ev_path.exists():
        raise FileNotFoundError(f"required table missing: {ev_path}")
    out: dict[str, pd.DataFrame | None] = {
        "evaluations": validate_evaluations(_read_csv(ev_path)),
        "forced_choice": None,
        "principle": None,
    }
    for name, fn in (("forced_choice", validate_forced_choice), ("principle", validate_principle)):
        p = d / f"{name}.csv"
        if p.exists():
            raw = _read_csv(p)
            if len(raw):
                out[name] = fn(raw)
    fc = out["forced_choice"]
    if fc is not None:
        bc = out["evaluations"].drop_duplicates("base_cv_id").set_index("base_cv_id")["base_country"]
        probs = []
        for side in ("cv_a", "cv_b"):
            m = fc[side].map(bc)
            bad = m.notna() & (m.astype("string") != fc["base_country"].astype("string")).fillna(True)
            if bad.any():
                probs.append(f"{int(bad.sum())} forced-choice row(s) whose base_country differs from the "
                             f"evaluations base_country of {side}")
        if probs:
            raise SchemaError("processed tables", probs)
    revs = {}
    for name, t in out.items():
        if t is not None and "model_revision" in t.columns:
            for alias, g in t.groupby("model_alias", observed=True):
                revs.setdefault(str(alias), set()).update(g["model_revision"].dropna().astype(str).unique())
    mixed = sorted(a for a, r in revs.items() if len(r) > 1)
    if mixed:
        raise SchemaError("processed tables", [f"model_alias with different model_revision values across tables "
                                               f"(mixed run): {mixed}"])
    return out


def all_mock(tables: dict[str, pd.DataFrame | None]) -> bool:
    """True if every row of every loaded table has ``is_mock == True``."""
    return all(bool(t["is_mock"].fillna(False).all()) for t in tables.values() if t is not None)


def any_mock(tables: dict[str, pd.DataFrame | None]) -> bool:
    """True if any row of any loaded table has ``is_mock == True``."""
    return any(bool(t["is_mock"].fillna(False).any()) for t in tables.values() if t is not None)


def mixed_mock(tables: dict[str, pd.DataFrame | None]) -> bool:
    """True if mock and non-mock rows are mixed (a contamination warning)."""
    vals = set()
    for t in tables.values():
        if t is not None:
            vals |= set(t["is_mock"].dropna().astype(bool).unique().tolist())
    return len(vals) > 1
