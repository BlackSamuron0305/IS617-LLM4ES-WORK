"""Build and check the prompts of the Schengen-visa (Estonia) experiment.

This script only reads the files under experiment/ and puts the prompts together. It
never calls a model. The runner that sends the prompts is pipeline/run_models.py; it
refuses real calls unless the team has approved them explicitly (CLAUDE.md, "Compute and
models").

The base design is blocks 1 to 3. Each other row of experiment/prompts/variants.csv is a
variant that changes one thing and is built as block 4.

Usage:
    python -m pipeline.build_runs                 check everything and print the counts
    python -m pipeline.build_runs --example       also print one complete run
    python -m pipeline.build_runs --write FILE    also write all prompts to FILE (JSON lines)
"""

import argparse
import json
import re
import sys

from pipeline import common, filter_applicants
from pipeline.common import EXPERIMENT

BASE_VARIANT = "base"
# Which guidance version a run gets: the paragraph on nationality (section 6) is empty, or one of the
# rule files in experiment/policy/.
WITHOUT_RULE = "without_nationality_rule"
RULE_FILES = {"nationality_rule", "regulation_rule", "info_rule"}
WORDINGS = (1, 2, 3)
RULE_PLACEHOLDER = "{nationality_rule}"
POLICY_PLACEHOLDER = "{policy}"
DEFAULT_ANSWER_KEYS = ("visa_score", "reason")
SCORE_KEYS = {"visa_score": "visa", "risk_score": "risk"}
GROUPS = ("arab", "placebo")
# The three wealth groups the Arab League countries are sorted into before any run
# (World Bank income classification; see experiment/countries/README.md).
WEALTH_GROUPS = ("rich", "normal", "poor")
# The columns of countries/official_rules.csv that describe the rules in force. The experiment rests on
# these being the same for every nationality that needs the visa.
RULE_COLUMNS = ("visa_needed", "application_form", "fee_eur", "legal_test", "nationality_is_a_ground_in_art_32",
                "means_per_day_eur", "insurance_min_eur", "entry_ban_or_visa_measure_2026_11_01")
# Blocks 1 and 2 use each applicant's own savings. Block 3 repeats block 1 with the other savings levels,
# once per wording, to measure how the answers react to money. Block 4 holds the variants.
REPETITIONS = {1: 5, 2: 5, 3: 1, 4: 1, 5: 5, 6: 5, 7: 5, 8: 5}
VARIANT_BLOCK = 4
# Blocks 7 and 8 (branch bias-deep-dive): the negative applicants, each with one clear ground for refusal, without and with the
# paragraph on nationality. They have their own template (more lines are placeholders).
TEMPLATES = {"main": "applicants/application_template.txt", "boundary": "applicants/application_template.txt",
             "negative": "applicants/application_template_negative.txt"}
# Blocks 5 and 6 (added 2026-11-02, experiment/deviations.md D4): the boundary applicants, each with three mild
# points, without and with the paragraph on nationality. Blocks 1 to 4 use the main applicants only.
# A removed field with fewer distinct values than this (sex, civil status) is made of common words and
# cannot be searched for in a prompt.
MIN_DISTINCT_TO_SEARCH = 6


def read_text(relative):
    return common.read_text(EXPERIMENT / relative)


def read_table(relative):
    return common.read_table(EXPERIMENT / relative)


def build_policy(guidance_file, rule=None):
    # The guidance with the paragraph on nationality (section 6) empty, or filled with one rule file.
    policy = read_text(f"policy/{guidance_file}")
    if policy.count(RULE_PLACEHOLDER) != 1:
        raise ValueError(f"{guidance_file} must contain {RULE_PLACEHOLDER} exactly once")
    text = read_text(f"policy/{rule}.txt").rstrip("\n") if rule else ""
    return policy.replace(RULE_PLACEHOLDER, text).rstrip("\n") + "\n"


_AED_PER_EUR = []


def aed_per_eur():
    # The exchange rate assumed for the experiment (costs/cost_assumptions.csv, item eur_to_aed).
    if not _AED_PER_EUR:
        rows = {r["item"]: r for r in read_table("costs/cost_assumptions.csv")}
        _AED_PER_EUR.append(float(rows["eur_to_aed"]["value"]))
    return _AED_PER_EUR[0]


def application_template(applicant):
    # The layout of the application of this applicant (it depends on the applicant set).
    return read_text(TEMPLATES[applicant["applicant_set"]])


def build_application(template, applicant, nationality, savings=None):
    text = template
    if savings is not None:
        applicant = dict(applicant, savings=savings)
    # Calculated by the case system, the same for every nationality: the funds in euros and the funds the
    # Estonian rule requires for the stay (EUR 70 per day; the template states the rate, check_rules checks it).
    applicant = dict(applicant, savings_eur=f"{round(int(applicant['savings']) / aed_per_eur()):,}",
                     required_eur=f"{70 * int(applicant['stay_days']):,}")
    for column, value in applicant.items():
        text = text.replace("{{" + column.upper() + "}}", value)
    text = text.replace("{nationality}", nationality["demonym"])
    text = text.replace("{travel_document}", nationality["travel_document"])
    return text.rstrip("\n")


def leftover_placeholders(text):
    return re.findall(r"\{\{[A-Z_]+\}\}|\{[a-z_]+\}", text)


def answer_block(task, first_key):
    marker = f'- "{first_key}"'
    return task[task.index(marker):] if marker in task else None


def load_variants():
    variants = {}
    for row in read_table("prompts/variants.csv"):
        row["answer_keys"] = tuple(row["answer_keys"].split(";"))
        variants[row["variant"]] = row
    return variants


def wanted_variants(which):
    # None: the base design only. "all": every row of variants.csv. Otherwise a list of names.
    names = list(load_variants())
    if which is None:
        return [BASE_VARIANT]
    if which == "all":
        return names
    unknown = [v for v in which if v not in names]
    if unknown:
        raise ValueError(f"unknown variant(s) {unknown}; experiment/prompts/variants.csv has: {', '.join(names)}")
    return list(which)


def check_filter(problems, applicants, nationalities, template):
    # applicants.csv must be what the filter gives, and no value of a removed field may reach a prompt.
    full = read_table("applicants/applicants_full.csv")
    kept, filtered, removed = filter_applicants.filter_rows(full, filter_applicants.load_filter())
    if filtered != applicants:
        problems.append("applicants.csv is not what field_filter.csv gives for applicants_full.csv "
                        "(run python -m pipeline.filter_applicants)")
    for column in removed:
        values = {row[column] for row in full}
        if len(values) < MIN_DISTINCT_TO_SEARCH:
            continue
        for applicant in applicants:
            application = build_application(application_template(applicant), applicant, nationalities[0])
            for row in full:
                if row["applicant_id"] == applicant["applicant_id"] and row[column] and row[column] in application:
                    problems.append(f"{applicant['applicant_id']}: removed field {column} occurs in the application")


def check_rules(problems, nationalities, guidance_texts):
    rules = read_table("countries/official_rules.csv")
    if {r["country"] for r in rules} != {n["country"] for n in nationalities}:
        problems.append("official_rules.csv and applicant_nationalities.csv list different countries")
    needs_visa = {n["country"]: n["visa_required"] for n in nationalities}
    if set(needs_visa.values()) - {"yes", "no"}:
        problems.append("visa_required must be yes or no for every nationality")
    in_scope = [r for r in rules if needs_visa.get(r["country"]) == "yes"]
    for column in RULE_COLUMNS:
        if len({r[column] for r in in_scope}) != 1:
            problems.append(f"official_rules.csv: {column} is not the same for every nationality that needs the visa")
    for r in rules:
        if needs_visa.get(r["country"]) == "no" and not r["visa_needed"].startswith("none"):
            problems.append(f"official_rules.csv: {r['country']} is visa-exempt but visa_needed says {r['visa_needed']!r}")
    if in_scope:
        # The amounts the guidance and the application state must be the amounts in the table.
        means, insurance = in_scope[0]["means_per_day_eur"], int(in_scope[0]["insurance_min_eur"])
        if means != "70" or f"EUR {means} per day" not in read_text("applicants/application_template.txt"):
            problems.append("application_template.txt and build_application assume EUR 70 per day, "
                            "which official_rules.csv does not say")
        for name, text in guidance_texts.items():
            if f"EUR {means} for each day" not in text:
                problems.append(f"{name}: does not state EUR {means} per day as official_rules.csv does")
            if f"EUR {insurance:,}" not in text:
                problems.append(f"{name}: does not state the insurance minimum EUR {insurance:,}")


def build_runs(which=None):
    all_applicants = read_table("applicants/applicants.csv")
    applicants = [a for a in all_applicants if a["applicant_set"] == "main"]
    boundary = [a for a in all_applicants if a["applicant_set"] == "boundary"]
    negative = [a for a in all_applicants if a["applicant_set"] == "negative"]
    nationalities = read_table("countries/applicant_nationalities.csv")
    variants = load_variants()
    chosen = wanted_variants(which)

    problems = []
    check_filter(problems, all_applicants, nationalities, None)

    # Checks that hold for every variant of the files, not only the chosen ones.
    guidance_texts = {}
    for variant in variants.values():
        guidance = variant["guidance"]
        if variant["rule"] and variant["rule"] not in RULE_FILES:
            problems.append(f"{variant['variant']}: unknown rule {variant['rule']!r}")
        if guidance and guidance not in guidance_texts:
            guidance_texts[guidance] = build_policy(guidance)
    for guidance, text in guidance_texts.items():
        if "nationality" in text.lower():
            problems.append(f"{guidance} without a rule mentions nationality")
        if "\n6. Nationality" in text:
            problems.append(f"{guidance} without a rule still has section 6")
    base_rule = read_text("policy/nationality_rule.txt").rstrip("\n")
    with_rule = build_policy(variants[BASE_VARIANT]["guidance"], "nationality_rule")
    if with_rule.replace(base_rule, "").rstrip("\n") + "\n" != guidance_texts[variants[BASE_VARIANT]["guidance"]]:
        problems.append("the two versions of the guidance differ by more than nationality_rule.txt")

    for nationality in nationalities:
        if nationality["group"] not in GROUPS:
            problems.append(f"{nationality['country']}: unknown group {nationality['group']!r}")
        if nationality["wealth_group"] not in WEALTH_GROUPS:
            problems.append(f"{nationality['country']}: unknown wealth group {nationality['wealth_group']!r}")
    if len({n["demonym"] for n in nationalities}) != len(nationalities):
        problems.append("two nationalities share a demonym")
    check_rules(problems, nationalities, guidance_texts)

    savings_levels = sorted({a["savings"] for a in applicants}, key=int)
    runs = []
    for name in chosen:
        variant = variants[name]
        main_prompt = read_text(f"prompts/{variant['main_prompt']}")
        keys = variant["answer_keys"]
        score_key = next((k for k in keys if k in SCORE_KEYS), None)
        if score_key is None:
            problems.append(f"{name}: answer_keys has no score key")
            continue
        if bool(variant["guidance"]) != (POLICY_PLACEHOLDER in main_prompt) or main_prompt.count(POLICY_PLACEHOLDER) > 1:
            problems.append(f"{name}: {POLICY_PLACEHOLDER} in the main prompt does not match the guidance column")
        tasks = {n: read_text(f"prompts/{variant['wordings']}/task_wording_{n}.txt") for n in WORDINGS}
        for n, task in tasks.items():
            if task.count("{application}") != 1:
                problems.append(f"{name}: task_wording_{n}.txt must contain {{application}} exactly once")
            for key in keys:
                if f'"{key}"' not in task:
                    problems.append(f"{name}: task_wording_{n}.txt does not ask for {key}")
        blocks_of_answer = {answer_block(task, keys[0]) for task in tasks.values()}
        if None in blocks_of_answer or len(blocks_of_answer) != 1:
            problems.append(f"{name}: the answer format differs between the wordings")

        if name == BASE_VARIANT:
            versions = ((1, WITHOUT_RULE, None, "own", applicants), (2, "with_nationality_rule", "nationality_rule", "own", applicants),
                        (3, WITHOUT_RULE, None, "others", applicants),
                        (5, WITHOUT_RULE, None, "own", boundary), (6, "with_nationality_rule", "nationality_rule", "own", boundary),
                        (7, WITHOUT_RULE, None, "own", negative), (8, "with_nationality_rule", "nationality_rule", "own", negative))
        else:
            rule = variant["rule"] or None
            versions = ((VARIANT_BLOCK, f"with_{rule}" if rule else WITHOUT_RULE, rule, "own", applicants),)
        for block, version, rule, which_levels, these in versions:
            if variant["guidance"]:
                system = main_prompt.replace(POLICY_PLACEHOLDER, build_policy(variant["guidance"], rule)).rstrip("\n") + "\n"
            else:
                system = main_prompt.rstrip("\n") + "\n"
            for applicant in these:
                template = application_template(applicant)
                levels = ([applicant["savings"]] if which_levels == "own"
                          else [x for x in savings_levels if x != applicant["savings"]])
                for savings in levels:
                    reference = build_application(template, applicant, nationalities[0], savings).split("\n")
                    for nationality in nationalities:
                        application = build_application(template, applicant, nationality, savings)
                        demonym = nationality["demonym"]
                        # An application may show the nationality in two lines only, and two
                        # nationalities may differ in those two lines only.
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
                            prefix = f"b{block}" if name == BASE_VARIANT else f"v_{name}"
                            runs.append({
                                "run_id": f"{prefix}__{applicant['applicant_id']}__s{savings}__{nationality['iso2']}__w{n}",
                                "block": block,
                                "variant": name,
                                "policy_version": version,
                                "answer_keys": keys,
                                "score_key": score_key,
                                "applicant_id": applicant["applicant_id"],
                                "file_profile": applicant["file_profile"],
                                "indicator": applicant["indicator"],
                                "savings": savings,
                                "country": nationality["country"],
                                "demonym": demonym,
                                "group": nationality["group"],
                                "wealth_group": nationality["wealth_group"],
                                "visa_required": nationality["visa_required"],
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
    parser.add_argument("--variants", action="store_true", help="also build and count every variant")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    runs, applicants, nationalities, problems = build_runs("all" if args.variants else None)

    groups = {}
    for nationality in nationalities:
        groups[nationality["group"]] = groups.get(nationality["group"], 0) + 1
    print(f"applicants:       {len(applicants)} main + {sum(a['applicant_set'] == 'boundary' for a in read_table('applicants/applicants.csv'))} boundary")
    print(f"nationalities:    {len(nationalities)}  {groups}")
    print(f"  of which need the visa: {sum(n['visa_required'] == 'yes' for n in nationalities)}")
    wealth = {g: sum(n["group"] == "arab" and n["wealth_group"] == g for n in nationalities) for g in WEALTH_GROUPS}
    print(f"wealth groups of the Arab League nationalities: {wealth}")
    print(f"wordings:         {len(WORDINGS)}")
    print(f"{'block':7}{'variant':26}{'guidance':28}{'prompts':>9}{'reps':>6}{'runs per model':>16}")
    total_runs = total_prompts = 0
    seen = []
    for run in runs:
        key = (run["block"], run["variant"] if run["block"] == VARIANT_BLOCK else BASE_VARIANT, run["policy_version"])
        if key not in seen:
            seen.append(key)
    for block, variant, version in seen:
        in_group = [r for r in runs if r["block"] == block and r["policy_version"] == version
                    and (block != VARIANT_BLOCK or r["variant"] == variant)]
        n_runs = sum(r["repetitions"] for r in in_group)
        total_runs += n_runs
        total_prompts += len(in_group)
        print(f"{block:<7}{variant:26}{version:28}{len(in_group):>9}{REPETITIONS[block]:>6}{n_runs:>16}")
    print(f"{'total':61}{total_prompts:>9}{'':6}{total_runs:>16}")
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
