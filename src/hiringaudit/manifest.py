"""Provenance: environment, git state, package versions, input hashes."""

from __future__ import annotations

import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path

from . import __version__

PACKAGES = ("numpy", "pandas", "scipy", "statsmodels", "matplotlib", "pydantic",
            "jsonschema", "pyarrow", "tqdm", "openai", "anthropic", "google-genai", "transformers",
            "torch")


def package_versions() -> dict[str, str | None]:
    out: dict[str, str | None] = {"hiringaudit": __version__}
    for p in PACKAGES:
        try:
            out[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            out[p] = None
    return out


def _git(args: list[str], cwd: Path) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def git_state(root: Path) -> dict:
    commit = _git(["rev-parse", "HEAD"], root)
    status = _git(["status", "--porcelain"], root)
    return {"commit": commit, "dirty": bool(status) if status is not None else None}


TRACKED_DIRS = ("src", "config", "prompts", "stimuli")


def package_root() -> Path:
    """The repository that contains the imported hiringaudit package (src/hiringaudit/..)."""
    return Path(__file__).resolve().parents[2]


def code_sha256() -> str:
    """SHA-256 over the source of the imported hiringaudit package (review N2)."""
    import hashlib

    pkg = Path(__file__).resolve().parent
    h = hashlib.sha256()
    for p in sorted(pkg.rglob("*.py")):
        h.update(str(p.relative_to(pkg)).replace("\\", "/").encode())
        h.update(p.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def uncommitted_paths(root: Path, dirs=TRACKED_DIRS) -> list[str] | None:
    """Modified OR untracked files under ``dirs`` (``git status --porcelain``).

    Returns None when git is unavailable or ``root`` is not a git work tree
    (provenance cannot be verified then).
    """
    if _git(["rev-parse", "--is-inside-work-tree"], root) != "true":
        return None
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--", *dirs], cwd=root,
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return [line[3:] for line in r.stdout.splitlines() if line.strip()]


def environment(root: Path) -> dict:
    return {
        "python": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git": git_state(root),
        "package_root": str(package_root()),
        "package_git": git_state(package_root()),
        "code_sha256": code_sha256(),
        "packages": package_versions(),
    }
