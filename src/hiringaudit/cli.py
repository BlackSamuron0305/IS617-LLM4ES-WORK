"""Command-line interface: ``python -m hiringaudit <command>``.

Commands
    validate-stimuli   check the two stimulus tables (stimuli/cvs.csv, stimuli/nationalities.csv),
                       every rendered CV x nationality combination, job ads and prompts;
                       exit code 1 on any violation
    plan               call counts by model x condition and a rough token estimate (--run <name>)
    run                call the models (--run <name>; real providers need --allow-real-calls)
    parse              raw JSONL -> processed CSV tables
    analyze            hand processed tables to hiringaudit.analysis.run_analysis
    manifest           show a run manifest and its coverage, or the environment
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .logging_utils import get_logger, setup_logging
from .paths import ProjectPaths

log = get_logger("cli")

EXIT_OK, EXIT_FAIL, EXIT_REFUSED, EXIT_ABORTED = 0, 1, 2, 3


def _paths(args) -> ProjectPaths:
    return ProjectPaths.from_root(args.root)


def cmd_validate_stimuli(args) -> int:
    from .validation import validate_stimuli

    rep = validate_stimuli(_paths(args))
    print(rep.summary())
    print("VALIDATION PASSED" if rep.ok else "VALIDATION FAILED")
    return EXIT_OK if rep.ok else EXIT_FAIL


REMOVED_CONFIG_FLAG = ("--config was removed: experiment configs are the rows of config/runs.csv. "
                       "Use --run <name>, e.g. --run mock, --run pilot or --run main.")


class UsageError(Exception):
    pass


def _load(args, validate_stimuli: bool = True):
    from .config import RunConfigError
    from .csvio import TableError
    from .prompts import PromptError
    from .runner import load_experiment

    if getattr(args, "config", None):
        raise UsageError(REMOVED_CONFIG_FLAG)
    if not args.run:
        raise UsageError("--run <name> is required (a run of config/runs.csv: mock, pilot or main)")
    try:
        return load_experiment(args.run, _paths(args), run_id=args.run_id, validate_stimuli=validate_stimuli)
    except (RunConfigError, TableError, PromptError) as e:
        raise UsageError(str(e)) from e


def cmd_plan(args) -> int:
    from .runner import make_plan

    print(make_plan(_load(args)).format())
    return EXIT_OK


def cmd_run(args) -> int:
    from .runner import (RealCallsNotAllowed, RunAborted, RunConfigMismatch, RunIdPolicyError, RunOptions,
                         make_plan, run_experiment)

    exp = _load(args)
    models = args.models.split(",") if args.models else None
    if not exp.is_mock or not args.quiet:
        print(make_plan(exp).format())
        print()
    try:
        summary = run_experiment(exp, RunOptions(allow_real_calls=args.allow_real_calls, limit=args.limit,
                                                 models=models, workers=args.workers,
                                                 show_progress=not args.quiet))
    except (RealCallsNotAllowed, RunConfigMismatch, RunIdPolicyError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return EXIT_REFUSED
    except RunAborted as e:
        print(f"ABORTED: {e}", file=sys.stderr)
        return EXIT_ABORTED
    print(f"run {summary.run_id}: {summary.status}; {summary.written} records written, "
          f"{summary.already_recorded} already present, {summary.planned} planned in scope")
    print(f"parse status: {summary.parse_status_counts}")
    for model, verdict in summary.stopped_models.items():
        print(f"TECHNICAL STOP: {model} stopped after {verdict['evaluated_at_n']} calls with "
              f"{100 * verdict['non_ok_share']:.1f}% non-ok (> {100 * verdict['max_non_ok_share']:.0f}%)")
    print(f"raw output: {summary.raw_dir}")
    return EXIT_OK


def cmd_parse(args) -> int:
    from .config import load_nationalities, load_text_flags
    from .parse_outputs import ParserMismatch, parse_outputs

    paths = _paths(args)
    try:
        summary = parse_outputs(paths.raw_run_dir(args.run_id), paths.processed_run_dir(args.run_id),
                                load_nationalities(paths.nationalities_file),
                                load_text_flags(paths.text_flags_file), text_flags_path=paths.text_flags_file,
                                exploratory=args.exploratory)
    except ParserMismatch as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return EXIT_REFUSED
    print(json.dumps({k: summary[k] for k in ("run_id", "parse_mode", "n_raw_records", "n_records", "rows",
                                              "parse_status_counts", "corrupt_raw_lines")}, indent=2))
    if summary.get("WARNING"):
        print(summary["WARNING"])
    print(f"processed tables: {summary['processed_dir']}")
    return EXIT_OK


def cmd_analyze(args) -> int:
    """Blind by default (review H1 / A15); ``--unblind`` asks run_analysis to unblind,
    and run_analysis itself enforces the preregistration freeze check."""
    paths = _paths(args)
    try:
        from .analysis import run_analysis  # owned by the statistician
    except ImportError as e:
        print(f"The analysis module is not available (hiringaudit.analysis.run_analysis): {e}. "
              f"It is maintained separately in src/hiringaudit/analysis/.", file=sys.stderr)
        return EXIT_FAIL
    config: dict = {}
    if args.config:
        if str(args.config).lower().endswith((".yaml", ".yml")):
            print("REFUSED: analyze --config takes a JSON file (YAML is no longer read); the confirmatory "
                  "settings are config/analysis_settings.csv", file=sys.stderr)
            return EXIT_REFUSED
        with open(args.config, encoding="utf-8") as fh:
            config = dict(json.load(fh) or {})
    if args.unblind:
        config.update({"unblind": True, "blind": False})
    else:
        config.update({"unblind": False, "blind": True})
    # Blind and unblinded outputs never share a directory (a blind pilot folder must
    # not contain per-origin tables left over from another mode).
    mode_dir = "unblinded" if args.unblind else "blind"
    out_dir = Path(args.out_dir) if args.out_dir else paths.results_run_dir(args.run_id) / mode_dir
    try:
        from .analysis.settings import UnblindingError
    except ImportError:  # pragma: no cover - older analysis module
        UnblindingError = PermissionError  # noqa: N806
    try:
        # root: the freeze check and the unblinding log refer to this data root (review N1 d)
        run_analysis(paths.processed_run_dir(args.run_id), out_dir, config, root=paths.root)
    except (UnblindingError, RuntimeError) as e:
        msg = " ".join(str(e).split())
        print(f"REFUSED ({type(e).__name__}): {msg}", file=sys.stderr)
        return EXIT_REFUSED
    print(f"analysis output ({'UNBLINDED' if args.unblind else 'blind'}): {out_dir}")
    return EXIT_OK


def cmd_manifest(args) -> int:
    paths = _paths(args)
    if args.run_id:
        path = paths.raw_run_dir(args.run_id) / "run_manifest.json"
        if not path.exists():
            print(f"no manifest at {path}", file=sys.stderr)
            return EXIT_FAIL
        man = json.loads(path.read_text(encoding="utf-8"))
        brief = {k: man.get(k) for k in ("run_id", "experiment_id", "is_mock", "WARNING", "created_utc",
                                         "config_hash", "input_file_sha256", "parser_version",
                                         "parser_fingerprint", "n_planned_calls", "model_provenance",
                                         "fc_design_summary", "stop_rule")}
        brief["sessions"] = [{k: s.get(k) for k in ("started_utc", "ended_utc", "status", "n_written",
                                                     "parse_status_counts")} for s in man.get("sessions", [])]
        if args.config:
            raise UsageError(REMOVED_CONFIG_FLAG)
        if args.run:
            from .runner import coverage

            brief["coverage"] = coverage(_load(args, validate_stimuli=False))
        print(json.dumps(brief, indent=2, default=str))
        return EXIT_OK
    from .manifest import environment
    from .prompts import SYSTEM_TEMPLATE_ID, load_library
    from .utils import sha256_text_file

    lib = load_library(paths.prompts_dir)
    templates = {SYSTEM_TEMPLATE_ID: lib.system_sha256, **{t: x.sha256 for t, x in sorted(lib.templates.items())}}
    inputs = (paths.cv_table_file, paths.nationalities_file, paths.cv_template_file, paths.jobs_file,
              paths.prompt_parts_file, paths.prompt_recipes_file, paths.principle_items_file)
    info = {"environment": environment(paths.root), "prompt_templates": templates,
            "input_files": {f.name: sha256_text_file(f) for f in inputs if f.exists()}}
    print(json.dumps(info, indent=2, default=str))
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m hiringaudit",
                                description="Counterfactual audit of LLM CV screening (synthetic data; not a hiring tool).")
    p.add_argument("--root", default=None, help="repository root (default: auto-detect)")
    p.add_argument("--log-level", default="INFO")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate-stimuli", help="validate the two stimulus tables, job ads and prompts")
    v.set_defaults(func=cmd_validate_stimuli)

    for name, func, helptext in (("plan", cmd_plan, "print call counts and a rough token estimate"),
                                 ("run", cmd_run, "run one run of config/runs.csv")):
        s = sub.add_parser(name, help=helptext)
        s.add_argument("--run", default=None, metavar="NAME",
                       help="a run of config/runs.csv (column 'run'): mock, pilot or main")
        s.add_argument("--config", default=None, help=argparse.SUPPRESS)   # removed; clear error
        s.add_argument("--run-id", default=None,
                       help="default: the run's run_id column or <experiment_id>__<hash of the inputs>")
        if name == "run":
            s.add_argument("--allow-real-calls", action="store_true",
                           help="required for any non-mock provider (costs money / cluster time)")
            s.add_argument("--limit", type=int, default=None, help="make at most N calls in this session")
            s.add_argument("--models", default=None, help="comma-separated aliases to run in this session")
            s.add_argument("--workers", type=int, default=None, help="override the configured concurrency")
            s.add_argument("--quiet", action="store_true", help="no progress bar; skip the plan for mock runs")
        s.set_defaults(func=func)

    pa = sub.add_parser("parse", help="raw responses -> processed tables")
    pa.add_argument("--run-id", required=True)
    pa.add_argument("--exploratory", action="store_true",
                    help="allow a parser that differs from the run's recorded one; writes to <run_id>__exploratory")
    pa.set_defaults(func=cmd_parse)

    an = sub.add_parser("analyze", help="run the statistician's analysis on processed tables")
    an.add_argument("--run-id", required=True)
    an.add_argument("--out-dir", default=None, help="default: results/<run_id>/blind or results/<run_id>/unblinded")
    an.add_argument("--config", default=None,
                    help="optional JSON file passed to run_analysis as `config` (confirmatory keys => EXPLORATORY "
                         "OVERRIDE)")
    an.add_argument("--unblind", action="store_true",
                    help="request unblinded output (run_analysis checks the preregistration freeze); default: blind")
    an.set_defaults(func=cmd_analyze)

    m = sub.add_parser("manifest", help="show a run manifest (with --run-id) or the environment/provenance")
    m.add_argument("--run-id", default=None)
    m.add_argument("--run", default=None, metavar="NAME",
                   help="with --run-id: also report planned vs recorded coverage for this run of config/runs.csv")
    m.add_argument("--config", default=None, help=argparse.SUPPRESS)   # removed; clear error
    m.set_defaults(func=cmd_manifest)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    setup_logging(args.log_level)
    try:
        return int(args.func(args) or 0)
    except UsageError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_REFUSED


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
