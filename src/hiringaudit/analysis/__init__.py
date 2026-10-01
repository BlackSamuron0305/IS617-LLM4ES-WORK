"""Statistical analysis for the hiring-audit study (statistician-owned subpackage).

Entry points (blind by default; see settings.py for unblinding):
    run_analysis(processed_dir, out_dir, config=None)          # config={"unblind": True} to unblind
    python -m hiringaudit.analysis --processed-dir DIR --out-dir DIR [--unblind]

The plan this code implements lives in ``analysis/statistical_analysis_plan.md``.
Synthetic data for tests and power analysis: ``hiringaudit.analysis.simulate``.
"""

from .pipeline import run_analysis
from .pipeline import _default_config as default_config
from .schema import MOCK_BANNER, SchemaError, load_processed
from .settings import OVERRIDE_BANNER, UnblindingError

__all__ = ["run_analysis", "default_config", "load_processed", "SchemaError", "UnblindingError",
           "MOCK_BANNER", "OVERRIDE_BANNER"]
