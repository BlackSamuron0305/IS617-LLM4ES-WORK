"""Build and check the prompts of the bank-onboarding experiment.

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
ANSWER_KEYS = ("risk_score", "risk_rating", "enhanced_checks", "recommendation", "reason")


def read_text(relative):
    return (EXPERIMENT / relative).read_text(encoding="utf-8")


def read_table(relative):
    with open(EXPERIMENT / relative, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_policy(version):
    policy = read_text("policy/bank_policy.txt")
    if policy.count(RULE_PLACEHOLDER) != 1:
        raise ValueError("bank_policy.txt must contain {nationality_rule} exactly once")
    rule = read_text("policy/nationality_rule.txt").rstrip("\n") if version == "with_nationality_rule" else ""
    return policy.replace(RULE_PLACEHOLDER, rule).rstrip("\n") + "\n"


def build_customer_file(template, customer, nationality):
    text = template
    for column, value in customer.items():
        text = text.replace("{{" + column.upper() + "}}", value)
    text = text.replace("{nationality}", nationality["demonym"])
    text = text.replace("{identity_document}", nationality["identity_document"])
    text = text.replace("{residence_status}", nationality["residence_status"])
    return text.rstrip("\n")


def leftover_placeholders(text):
    return re.findall(r"\{\{[A-Z_]+\}\}|\{[a-z_]+\}", text)


def build_runs():
    customers = read_table("customers/customers.csv")
    nationalities = read_table("countries/customer_nationalities.csv")
    template = read_text("customers/customer_file_template.txt")
    main_prompt = read_text("prompts/main_prompt.txt")
    tasks = {n: read_text(f"prompts/task_wording_{n}.txt") for n in WORDINGS}
    policies = {version: build_policy(version) for version in POLICY_VERSIONS}

    problems = []

    # The two policy versions may differ only by the rule paragraph.
    rule = read_text("policy/nationality_rule.txt").rstrip("\n")
    without_rule = policies["with_nationality_rule"].replace(rule, "").rstrip("\n") + "\n"
    if rule not in policies["with_nationality_rule"] or without_rule != policies["without_nationality_rule"]:
        problems.append("the two policy versions differ by more than nationality_rule.txt")
    if "nationality" in policies["without_nationality_rule"].lower():
        problems.append("the policy without the rule mentions nationality")

    # Every wording must ask for the same answer.
    for n, task in tasks.items():
        if task.count("{customer_file}") != 1:
            problems.append(f"task_wording_{n}.txt must contain {{customer_file}} exactly once")
        for key in ANSWER_KEYS:
            if f'"{key}"' not in task:
                problems.append(f"task_wording_{n}.txt does not ask for {key}")
    answer_blocks = {task[task.index('- "risk_score"'):] for task in tasks.values()}
    if len(answer_blocks) != 1:
        problems.append("the answer format differs between the wordings")

    runs = []
    for version in POLICY_VERSIONS:
        system = main_prompt.replace("{policy}", policies[version]).rstrip("\n") + "\n"
        for customer in customers:
            for nationality in nationalities:
                customer_file = build_customer_file(template, customer, nationality)
                demonym = nationality["demonym"]
                # A customer file may show the nationality in two lines only.
                if demonym != "German" and customer_file.count(demonym) != 2:
                    problems.append(f"{customer['customer_id']} / {demonym}: the demonym occurs "
                                    f"{customer_file.count(demonym)} times, expected 2")
                for n in WORDINGS:
                    user = tasks[n].replace("{customer_file}", customer_file)
                    for part in (system, user):
                        for placeholder in leftover_placeholders(part):
                            problems.append(f"unfilled placeholder {placeholder}")
                    runs.append({
                        "run_id": f"{version}__{customer['customer_id']}__{nationality['country']}__w{n}",
                        "policy_version": version,
                        "customer_id": customer["customer_id"],
                        "file_profile": customer["file_profile"],
                        "country": nationality["country"],
                        "demonym": demonym,
                        "group": nationality["group"],
                        "eu_high_risk_list": nationality["eu_high_risk_list"],
                        "wording": n,
                        "system": system,
                        "user": user,
                    })
    return runs, customers, nationalities, sorted(set(problems))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--example", action="store_true", help="print one complete run")
    parser.add_argument("--write", metavar="FILE", help="write all prompts as JSON lines")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    runs, customers, nationalities, problems = build_runs()

    groups = {}
    for nationality in nationalities:
        groups[nationality["group"]] = groups.get(nationality["group"], 0) + 1
    files = len(customers) * len(nationalities)
    per_version = files * len(WORDINGS)
    print(f"customers:        {len(customers)}")
    print(f"nationalities:    {len(nationalities)}  {groups}")
    print(f"customer files:   {files}")
    print(f"wordings:         {len(WORDINGS)}")
    print(f"policy versions:  {len(POLICY_VERSIONS)}")
    print(f"prompts per policy version: {per_version}")
    print(f"prompts in total:           {len(runs)}")
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
