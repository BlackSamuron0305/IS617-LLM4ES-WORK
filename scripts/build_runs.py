"""Build and check the prompts of the visitor-visa experiment.

This script only reads the files under experiment/ and puts the prompts together. It
never calls a model. A runner that sends requests does not exist yet; when one is
written it must refuse real calls unless the team has approved them explicitly
(CLAUDE.md, "Compute and models").

Usage:
    python scripts/build_runs.py                 check everything and print the counts
    python scripts/build_runs.py --example       also print one complete run
    python scripts/build_runs.py --write FILE    also write all prompts to FILE (JSON lines)
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

EXPERIMENT = Path(__file__).resolve().parent.parent / "experiment"
POLICY_VERSIONS = ("without_nationality_rule", "with_nationality_rule")
WORDINGS = (1, 2, 3)
RULE_PLACEHOLDER = "{nationality_rule}"
ANSWER_KEYS = ("risk_score", "risk_rating", "further_checks", "recommendation", "reason")
CHECK_LETTERS = "ABCDEF"
GROUPS = ("arab", "placebo")
# The three wealth groups the Arab League countries are sorted into before any run
# (World Bank income classification; see experiment/countries/README.md).
WEALTH_GROUPS = ("rich", "normal", "poor")
# The columns of countries/official_rules.csv that describe the rules in force. The
# experiment rests on these being the same for every nationality.
RULE_COLUMNS = ("visa_needed", "electronic_travel_authority_601", "evisitor_651", "application_form", "fee_aud",
                "legal_test", "on_a_risk_list_in_force", "entry_ban_or_travel_suspension_2026_10_10")
# Blocks 1 and 2 use each applicant's own savings. Block 3 repeats block 1 with the
# other savings levels, once per wording, to measure how the answers react to money.
REPETITIONS = {1: 5, 2: 5, 3: 1}


def read_text(relative):
    return (EXPERIMENT / relative).read_text(encoding="utf-8")


def read_table(relative):
    with open(EXPERIMENT / relative, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_policy(version):
    policy = read_text("policy/visa_guidance.txt")
    if policy.count(RULE_PLACEHOLDER) != 1:
        raise ValueError("visa_guidance.txt must contain {nationality_rule} exactly once")
    rule = read_text("policy/nationality_rule.txt").rstrip("\n") if version == "with_nationality_rule" else ""
    return policy.replace(RULE_PLACEHOLDER, rule).rstrip("\n") + "\n"


def build_application(template, applicant, nationality, savings=None):
    text = template
    if savings is not None:
        applicant = dict(applicant, savings=savings)
    for column, value in applicant.items():
        text = text.replace("{{" + column.upper() + "}}", value)
    text = text.replace("{nationality}", nationality["demonym"])
    text = text.replace("{travel_document}", nationality["travel_document"])
    return text.rstrip("\n")


def leftover_placeholders(text):
    return re.findall(r"\{\{[A-Z_]+\}\}|\{[a-z_]+\}", text)


def build_runs():
    applicants = read_table("applicants/applicants.csv")
    nationalities = read_table("countries/applicant_nationalities.csv")
    template = read_text("applicants/application_template.txt")
    main_prompt = read_text("prompts/main_prompt.txt")
    tasks = {n: read_text(f"prompts/base/task_wording_{n}.txt") for n in WORDINGS}
    policies = {version: build_policy(version) for version in POLICY_VERSIONS}

    problems = []

    # The two versions of the guidance may differ only by the rule paragraph.
    rule = read_text("policy/nationality_rule.txt").rstrip("\n")
    without_rule = policies["with_nationality_rule"].replace(rule, "").rstrip("\n") + "\n"
    if rule not in policies["with_nationality_rule"] or without_rule != policies["without_nationality_rule"]:
        problems.append("the two versions of the guidance differ by more than nationality_rule.txt")
    if "nationality" in policies["without_nationality_rule"].lower():
        problems.append("the guidance without the rule mentions nationality")
    for letter in CHECK_LETTERS:
        if f"\n{letter} - " not in policies["without_nationality_rule"]:
            problems.append(f"the guidance does not list further check {letter}")

    # Every wording must ask for the same answer.
    for n, task in tasks.items():
        if task.count("{application}") != 1:
            problems.append(f"task_wording_{n}.txt must contain {{application}} exactly once")
        for key in ANSWER_KEYS:
            if f'"{key}"' not in task:
                problems.append(f"task_wording_{n}.txt does not ask for {key}")
    answer_blocks = {task[task.index('- "risk_score"'):] for task in tasks.values()}
    if len(answer_blocks) != 1:
        problems.append("the answer format differs between the wordings")

    for nationality in nationalities:
        if nationality["group"] not in GROUPS:
            problems.append(f"{nationality['country']}: unknown group {nationality['group']!r}")
        if nationality["wealth_group"] not in WEALTH_GROUPS:
            problems.append(f"{nationality['country']}: unknown wealth group {nationality['wealth_group']!r}")
    if len({n["demonym"] for n in nationalities}) != len(nationalities):
        problems.append("two nationalities share a demonym")

    # The official rules must be the same for every nationality in the experiment.
    rules = read_table("countries/official_rules.csv")
    if {r["country"] for r in rules} != {n["country"] for n in nationalities}:
        problems.append("official_rules.csv and applicant_nationalities.csv list different countries")
    for column in RULE_COLUMNS:
        if len({r[column] for r in rules}) != 1:
            problems.append(f"official_rules.csv: {column} is not the same for every nationality")

    savings_levels = sorted({a["savings"] for a in applicants}, key=int)
    systems = {version: main_prompt.replace("{policy}", policies[version]).rstrip("\n") + "\n" for version in POLICY_VERSIONS}
    # (block, guidance version, which savings levels an applicant is shown with)
    blocks = ((1, "without_nationality_rule", "own"), (2, "with_nationality_rule", "own"), (3, "without_nationality_rule", "others"))

    runs = []
    for block, version, which in blocks:
        system = systems[version]
        for applicant in applicants:
            levels = [applicant["savings"]] if which == "own" else [x for x in savings_levels if x != applicant["savings"]]
            for savings in levels:
                reference = build_application(template, applicant, nationalities[0], savings).split("\n")
                for nationality in nationalities:
                    application = build_application(template, applicant, nationality, savings)
                    demonym = nationality["demonym"]
                    # An application may show the nationality in two lines only, and
                    # two nationalities may differ in those two lines only.
                    if application.count(demonym) != 2:
                        problems.append(f"{applicant['applicant_id']} / {demonym}: the demonym occurs "
                                        f"{application.count(demonym)} times, expected 2")
                    lines = application.split("\n")
                    differing = sum(a != b for a, b in zip(reference, lines))
                    if len(lines) != len(reference) or differing not in (0, 2):
                        problems.append(f"{applicant['applicant_id']} / {demonym}: differs from the first "
                                        f"nationality in {differing} lines, expected 2")
                    for n in WORDINGS:
                        user = tasks[n].replace("{application}", application)
                        for part in (system, user):
                            for placeholder in leftover_placeholders(part):
                                problems.append(f"unfilled placeholder {placeholder}")
                        runs.append({
                            "run_id": f"b{block}__{applicant['applicant_id']}__s{savings}__{nationality['iso2']}__w{n}",
                            "block": block,
                            "policy_version": version,
                            "applicant_id": applicant["applicant_id"],
                            "file_profile": applicant["file_profile"],
                            "indicator": applicant["indicator"],
                            "savings": savings,
                            "country": nationality["country"],
                            "demonym": demonym,
                            "group": nationality["group"],
                            "wealth_group": nationality["wealth_group"],
                            "wording": n,
                            "repetitions": REPETITIONS[block],
                            "system": system,
                            "user": user,
                        })
    if len({r["run_id"] for r in runs}) != len(runs):
        problems.append("two prompts share a run id")
    return runs, applicants, nationalities, sorted(set(problems))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--example", action="store_true", help="print one complete run")
    parser.add_argument("--write", metavar="FILE", help="write all prompts as JSON lines")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    runs, applicants, nationalities, problems = build_runs()

    groups = {}
    for nationality in nationalities:
        groups[nationality["group"]] = groups.get(nationality["group"], 0) + 1
    print(f"applicants:       {len(applicants)}")
    print(f"nationalities:    {len(nationalities)}  {groups}")
    wealth = {g: sum(n["group"] == "arab" and n["wealth_group"] == g for n in nationalities) for g in WEALTH_GROUPS}
    print(f"wealth groups of the Arab League nationalities: {wealth}")
    print(f"wordings:         {len(WORDINGS)}")
    print(f"{'block':7}{'guidance':28}{'prompts':>9}{'repetitions':>13}{'runs per model':>16}")
    total = 0
    for block in sorted(REPETITIONS):
        in_block = [r for r in runs if r["block"] == block]
        n_runs = len(in_block) * REPETITIONS[block]
        total += n_runs
        print(f"{block:<7}{in_block[0]['policy_version']:28}{len(in_block):>9}{REPETITIONS[block]:>13}{n_runs:>16}")
    print(f"{'total':35}{len(runs):>9}{'':13}{total:>16}")
    words = sorted(len((r["system"] + r["user"]).split()) for r in runs)
    print(f"words per prompt: {words[0]} to {words[-1]}")

    if args.example:
        example = next(r for r in runs if r["demonym"] == "Jordanian")
        print("\n" + "=" * 30 + " SYSTEM " + "=" * 30)
        print(example["system"])
        print("=" * 30 + " USER " + "=" * 32)
        print(example["user"])

    if args.write:
        with open(args.write, "w", encoding="utf-8", newline="\n") as f:
            for run in runs:
                f.write(json.dumps(run, ensure_ascii=False) + "\n")
        print(f"\nwrote {len(runs)} prompts to {args.write}")

    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for problem in problems[:20]:
            print("  -", problem)
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
