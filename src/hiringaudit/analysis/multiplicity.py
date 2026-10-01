"""Multiplicity adjustments (see analysis/multiple_testing_plan.md)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests


def _adjust(p, method: str) -> np.ndarray:
    p = np.asarray(p, float)
    out = np.full(p.shape, np.nan)
    ok = np.isfinite(p)
    if ok.any():
        out[ok] = multipletests(p[ok], method=method)[1]
    return out


def holm(p) -> np.ndarray:
    """Holm step-down FWER-adjusted p-values (NaN kept as NaN, not counted)."""
    return _adjust(p, "holm")


def bh(p) -> np.ndarray:
    """Benjamini-Hochberg FDR-adjusted p-values (q-values)."""
    return _adjust(p, "fdr_bh")


def adjust_within(df: pd.DataFrame, p_col: str, by: list[str] | None, method: str,
                  out_col: str) -> pd.DataFrame:
    """Add an adjusted p-value column, adjusting separately within ``by`` groups."""
    df = df.copy()
    fn = holm if method == "holm" else bh
    if not by:
        df[out_col] = fn(df[p_col].to_numpy())
    else:
        df[out_col] = np.nan
        for _, idx in df.groupby(by[0] if len(by) == 1 else by, observed=True).groups.items():
            df.loc[idx, out_col] = fn(df.loc[idx, p_col].to_numpy())
    return df
