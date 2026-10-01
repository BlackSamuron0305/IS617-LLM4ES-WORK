"""CSV and LaTeX (booktabs) table writers with mock-data labelling."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .schema import MOCK_BANNER

MOCK_BANNER_TEX = "SYNTHETIC MOCK DATA --- NOT RESULTS"

_TEX_ESC = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
            "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def tex_escape(s) -> str:
    return "".join(_TEX_ESC.get(ch, ch) for ch in str(s))


def _fmt(v, col: str, digits: int) -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)) or v is pd.NA:
        return "--"
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else "no"
    if isinstance(v, (int, np.integer)):
        return f"{int(v)}"
    if isinstance(v, (float, np.floating)):
        if col.startswith("p") or col.startswith("q_") or "_p" in col:
            return "<0.001" if v < 0.001 else f"{v:.3f}"
        if float(v).is_integer() and abs(v) >= 1 and col in ("n_cv", "calls", "valid_calls"):
            return f"{int(v)}"
        return f"{v:.{digits}f}"
    return tex_escape(v)


def _banners(mock) -> list[str]:
    if isinstance(mock, (list, tuple)):
        return list(mock)
    return [MOCK_BANNER] if mock else []


def write_csv(df: pd.DataFrame, path: Path, mock) -> Path:
    """CSV with one '# <banner>' line per banner (mock data, exploratory override) before the header."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        for b in _banners(mock):
            fh.write(f"# {b}\n")
        df.to_csv(fh, index=False)
    return path


def read_csv(path: str | Path) -> pd.DataFrame:
    """Read a table written by :func:`write_csv` (skips the leading banner lines)."""
    return pd.read_csv(path, skiprows=_banner_rows(path))


def _banner_rows(path) -> int:
    n = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("# "):
                break
            n += 1
    return n


def write_latex(df: pd.DataFrame, path: Path, mock, caption: str, label: str,
                digits: int = 2, col_labels: dict | None = None) -> Path:
    """booktabs tabular; each banner as a comment line, caption prefix and a bold row."""
    path.parent.mkdir(parents=True, exist_ok=True)
    banners = _banners(mock)
    cols = list(df.columns)
    heads = [tex_escape((col_labels or {}).get(c, c)) for c in cols]
    align = "".join("r" if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])
                    else "l" for c in cols)
    tex_b = [b.replace("\u2014", "---") for b in banners]
    cap = "".join(f"{b}. " for b in tex_b) + caption
    lines = [f"% {b}" for b in banners]
    lines += [r"\begin{table}[t]", r"\centering", r"\small",
              rf"\caption{{{tex_escape(cap)}}}", rf"\label{{{label}}}",
              rf"\begin{{tabular}}{{{align}}}", r"\toprule"]
    for b in tex_b:
        lines.append(rf"\multicolumn{{{len(cols)}}}{{l}}{{\textbf{{{tex_escape(b)}}}}} \\")
    if tex_b:
        lines.append(r"\midrule")
    lines.append(" & ".join(heads) + r" \\")
    lines.append(r"\midrule")
    for _, r in df.iterrows():
        lines.append(" & ".join(_fmt(r[c], c, digits) for c in cols) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
