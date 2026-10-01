"""Confirmatory settings, blinding gate, unblinding log and provenance (adversarial review H1, L12).

* The project root is passed as ``run_analysis(..., root=...)`` (default: the repository that
  contains this package). It can NOT be set through the run config (review round 2, N1a/b); nor
  can the confirmatory-settings path or the unblinding-log path: they are always
  ``<root>/config/analysis_settings.csv`` and ``<root>/results/unblinding_log.jsonl``.
* A run config that changes any confirmatory key is an EXPLORATORY OVERRIDE, and so is a
  confirmatory file that is not committed at HEAD or differs from the committed version.
* ``run_analysis`` is blind unless ``config["unblind"] is True``. Unblinding real data requires a
  valid freeze (N1c): ``preregistration.md`` and ``config/prereg_freeze.json`` both committed at
  HEAD and identical to the working tree; the freeze's ``preregistration_sha256`` equal to the
  SHA-256 of ``preregistration.md``; no unresolved "[TEAM DECISION REQUIRED" / "TO PIN BEFORE
  FREEZE" markers; ``config/analysis_settings.csv`` committed and unchanged. Data in which
  every row is mock may be unblinded without a freeze (outputs keep the mock banner).
* Every unblinded run is appended to ``<root>/results/unblinding_log.jsonl``.

SHA-256 values of text files are computed after normalising CRLF to LF, so a Windows
checkout gives the same hash as a Unix one.
"""

from __future__ import annotations

import copy
import getpass
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OVERRIDE_BANNER = "EXPLORATORY OVERRIDE — confirmatory settings changed"
PARSE_BANNER = "EXPLORATORY PARSE — tables re-parsed with a non-frozen parser"
PREREG_MARKERS = ("[TEAM DECISION REQUIRED", "TO PIN BEFORE FREEZE")
FORBIDDEN_KEYS = {
    "repo_root": "pass root= to run_analysis (CLI: --root) instead",
    "confirmatory_config": "the confirmatory settings are always <root>/config/analysis_settings.csv",
    "unblinding_log": "the unblinding log is always <root>/results/unblinding_log.jsonl",
    "r4_processed_dir": "removed: the greedy arm arrives in the same run via arm == 'greedy'",
}
CONFIRMATORY_FILE = "config/analysis_settings.csv"
SETTING_COLUMNS = ("setting", "value", "type", "description")
SETTING_TYPES = ("int", "float", "bool", "str", "list")
FREEZE_FILE = "config/prereg_freeze.json"
PREREG_FILE = "preregistration.md"
UNBLIND_LOG = "results/unblinding_log.jsonl"
PACKAGE_ROOT = Path(__file__).resolve().parents[3]

# Operational keys: they change what is run or written, not what is concluded.
OPERATIONAL_DEFAULTS: dict = {
    "unblind": False,
    "blind": None,                 # legacy: blind=True forces blind mode; blind=False alone never unblinds
    "make_figures": True,
    "run_mixedlm": True,
    "run_gee": True,
    "run_robustness": True,
    "min_cv_warning": 8,
}


class UnblindingError(PermissionError):
    """Raised when unblinded analysis of real data is requested without a valid freeze."""


def sha256_text(path: str | Path) -> str:
    b = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def _flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, key + "."))
        else:
            out[key] = v
    return out


def _merge(base: dict, over: dict | None) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _setting_value(raw: str, typ: str, where: str):
    v = raw.strip()
    if typ == "str":
        return v
    if typ == "list":
        return [x.strip() for x in v.split("|") if x.strip()]
    if typ == "bool":
        if v.lower() not in ("true", "false"):
            raise ValueError(f"{where}: expected true or false, got {raw!r}")
        return v.lower() == "true"
    try:
        return int(v) if typ == "int" else float(v)
    except ValueError as e:
        raise ValueError(f"{where}: expected {typ}, got {raw!r}") from e


def load_confirmatory(path: str | Path) -> dict:
    """Read config/analysis_settings.csv (setting, value, type, description) into the
    nested settings dict: a dotted setting name ``sesoi.overall_fit`` becomes
    ``{"sesoi": {"overall_fit": ...}}``; ``type`` is int, float, bool, str or list
    (" | "-separated). The ``version`` row describes the file and is dropped."""
    import csv

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"confirmatory analysis settings not found: {p}")
    with open(p, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        cols = list(reader.fieldnames or [])
        rows = [r for r in reader if any((v or "").strip() for v in r.values())]
    if cols[:len(SETTING_COLUMNS)] != list(SETTING_COLUMNS) or len(cols) != len(SETTING_COLUMNS):
        raise ValueError(f"{p}: columns must be {list(SETTING_COLUMNS)}, got {cols}")
    data: dict = {}
    for r in rows:
        name, typ = (r["setting"] or "").strip(), (r["type"] or "").strip()
        where = f"{p.name} [{name}]"
        if typ not in SETTING_TYPES:
            raise ValueError(f"{where}: type must be one of {SETTING_TYPES}, got {typ!r}")
        *parents, leaf = name.split(".")
        node = data
        for k in parents:
            node = node.setdefault(k, {})
            if not isinstance(node, dict):
                raise ValueError(f"{where}: {k} is both a setting and a group")
        if leaf in node:
            raise ValueError(f"{where}: duplicate setting")
        node[leaf] = _setting_value(r["value"] or "", typ, where)
    if "sesoi" not in data:
        raise ValueError(f"{p}: not a confirmatory analysis settings file (no 'sesoi.*' settings)")
    data.pop("version", None)
    return data


def git_committed_identical(root: Path, rel: str) -> tuple[bool, str]:
    """True if ``rel`` is committed at HEAD in the git repository at ``root`` and the working-tree
    file has the same content (line endings normalised). Returns (ok, reason)."""
    p = Path(root) / rel
    if not p.exists():
        return False, f"{rel} not found"
    try:
        r = subprocess.run(["git", "-C", str(root), "show", f"HEAD:{rel}"], capture_output=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as e:
        return False, f"git not available ({e})"
    if r.returncode != 0:
        return False, f"{rel} is not committed at HEAD"
    head = r.stdout.replace(b"\r\n", b"\n")
    work = p.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(head).hexdigest() != hashlib.sha256(work).hexdigest():
        return False, f"{rel} differs from the committed version"
    return True, f"{rel} committed and unchanged"


def resolve_config(user: dict | None, root: str | Path | None = None) -> tuple[dict, dict]:
    """Merge operational defaults, the confirmatory settings (<root>/config/analysis_settings.csv)
    and the user config.

    Returns (cfg, info) with info = {root, confirmatory_path, confirmatory_sha256, confirmatory_committed,
    overrides}. Forbidden keys (repo_root, confirmatory_config, unblinding_log) and unknown keys raise
    ValueError. A confirmatory file that is not committed at HEAD or differs from HEAD is an override.
    """
    user = dict(user or {})
    bad = sorted(set(user) & set(FORBIDDEN_KEYS))
    if bad:
        raise ValueError("analysis config key(s) not allowed: "
                         + "; ".join(f"'{k}' ({FORBIDDEN_KEYS[k]})" for k in bad))
    root = Path(root) if root is not None else PACKAGE_ROOT
    cpath = root / CONFIRMATORY_FILE
    conf = load_confirmatory(cpath)
    allowed = set(OPERATIONAL_DEFAULTS) | set(conf)
    unknown = sorted(set(user) - allowed)
    if unknown:
        raise ValueError(f"unknown analysis config key(s): {unknown}")
    flat_conf = _flatten(conf)
    user_conf = {k: v for k, v in user.items() if k in conf}
    overrides = sorted(k for k, v in _flatten(user_conf).items()
                       if k not in flat_conf or flat_conf[k] != v)
    committed, why = git_committed_identical(root, CONFIRMATORY_FILE)
    if not committed:
        overrides.append(f"{CONFIRMATORY_FILE} ({why})")
    cfg = _merge(_merge(OPERATIONAL_DEFAULTS, conf), user)
    cp = cfg.get("covariates_path")
    if cp and not Path(cp).is_absolute():
        cfg["covariates_path"] = str(root / cp)
    info = dict(root=root, confirmatory_path=cpath, confirmatory_sha256=sha256_text(cpath),
                confirmatory_committed=committed, confirmatory_status=why, overrides=overrides)
    return cfg, info


def blind_requested(cfg: dict) -> bool:
    if cfg.get("blind") is True:
        return True
    return cfg.get("unblind") is not True


def check_unblinding(root: Path, all_mock: bool) -> dict:
    """Verify the preregistration freeze (review H1, round-2 N1c). Returns {prereg_sha256, freeze_ok, reason}.

    Valid only if (i) preregistration.md and config/prereg_freeze.json are committed at HEAD and identical
    to the working tree, (ii) the freeze's preregistration_sha256 equals the SHA-256 of preregistration.md,
    (iii) preregistration.md has no unresolved markers, (iv) config/analysis_settings.csv is committed
    and unchanged. Mock-only data are exempt (the run proceeds and the reason is recorded).
    """
    root = Path(root)
    prereg = root / PREREG_FILE
    freeze = root / FREEZE_FILE
    cur = sha256_text(prereg) if prereg.exists() else None
    frozen = None
    if freeze.exists():
        try:
            frozen = json.loads(freeze.read_text(encoding="utf-8")).get("preregistration_sha256")
        except json.JSONDecodeError:
            frozen = None
    problems = []
    if not freeze.exists():
        problems.append(f"{FREEZE_FILE} not found")
    if cur is None:
        problems.append(f"{PREREG_FILE} not found")
    if cur and freeze.exists() and cur != frozen:
        problems.append("preregistration.md has changed since it was frozen (hash mismatch)")
    for rel in (PREREG_FILE, FREEZE_FILE, CONFIRMATORY_FILE):
        if (root / rel).exists():
            ok_rel, why = git_committed_identical(root, rel)
            if not ok_rel:
                problems.append(why)
    if cur:
        text = prereg.read_text(encoding="utf-8", errors="replace")
        found = [m for m in PREREG_MARKERS if m in text]
        if found:
            problems.append(f"{PREREG_FILE} still contains unresolved markers {found}")
    ok = not problems
    reason = "valid freeze: preregistration, freeze file and confirmatory config committed; hash matches" \
        if ok else "; ".join(problems)
    if not ok and not all_mock:
        raise UnblindingError(
            f"Unblinded analysis of non-mock data refused: {reason}. To freeze: resolve all markers in "
            f"{PREREG_FILE}, write {{\"preregistration_sha256\": \"<sha256 of {PREREG_FILE}, LF line endings>\"}} "
            f"to {FREEZE_FILE}, and commit both files and {CONFIRMATORY_FILE}. Otherwise run blind (the default).")
    return dict(prereg_sha256=cur, frozen_sha256=frozen, freeze_ok=ok,
                reason=reason if ok else f"{reason}; allowed because every input row is mock")


def append_unblinding_log(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, default=str) + "\n")


def provenance(root: Path) -> dict:
    """Git commit (+ dirty flag for analysis code/config) and SHA-256 of the analysis code."""
    code = sorted(Path(__file__).resolve().parent.glob("*.py"))
    h = hashlib.sha256()
    for f in code:
        h.update(f.name.encode())
        h.update(f.read_bytes().replace(b"\r\n", b"\n"))
    out = {"analysis_code_sha256": h.hexdigest(), "git_commit": None, "git_dirty": None,
           "code_git_commit": None, "code_git_dirty": None}
    code_dir = Path(__file__).resolve().parent

    def _git(args, cwd):
        r = subprocess.run(["git", "-C", str(cwd)] + args, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None

    try:
        out["git_commit"] = _git(["rev-parse", "HEAD"], root)
        st = _git(["status", "--porcelain", "--untracked-files=all", "--", "config", PREREG_FILE], root)
        out["git_dirty"] = None if st is None else bool(st)
        out["code_git_commit"] = _git(["rev-parse", "HEAD"], code_dir)
        st2 = _git(["status", "--porcelain", "--untracked-files=all", "--", "."], code_dir)
        out["code_git_dirty"] = None if st2 is None else bool(st2)
    except (OSError, subprocess.SubprocessError):
        pass
    return out


def unblinding_entry(info: dict, gate: dict, processed_dir, out_dir, mock: bool, prov: dict) -> dict:
    try:
        user = getpass.getuser()
    except Exception:  # noqa: BLE001
        user = "unknown"
    return dict(utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), user=user,
                prereg_sha256=gate.get("prereg_sha256"), freeze_ok=gate.get("freeze_ok"),
                confirmatory_config_sha256=info["confirmatory_sha256"], overrides=info["overrides"],
                input_dir=str(Path(processed_dir).resolve()), out_dir=str(Path(out_dir).resolve()),
                all_rows_mock=mock, git_commit=prov.get("git_commit"),
                analysis_code_sha256=prov.get("analysis_code_sha256"))
