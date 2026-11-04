"""Tests for the prompt builder (pipeline/build_runs.py) and the applicant filter. They call no model."""

import subprocess
import sys
import unittest

from pipeline import filter_applicants
from pipeline.build_runs import build_runs, load_variants
from pipeline.common import EXPERIMENT, ROOT, read_table


class BuildRunsTest(unittest.TestCase):
    def test_counts_and_checks(self):
        runs, applicants, nationalities, problems = build_runs()
        self.assertEqual(problems, [])
        self.assertEqual(len(runs), 17472)
        self.assertEqual(sum(r["repetitions"] for r in runs), 49920)
        self.assertEqual(len({r["run_id"] for r in runs}), 17472)
        self.assertEqual({r["variant"] for r in runs}, {"base"})

    def test_every_variant_builds_and_has_its_own_run_ids(self):
        runs, _, _, problems = build_runs("all")
        self.assertEqual(problems, [])
        variants = load_variants()
        self.assertEqual({r["variant"] for r in runs}, set(variants))
        self.assertEqual(len(runs), 17472 + sum(len(read_table(EXPERIMENT / "countries" / v["nationality_set"])) * 90 if v["nationality_set"] else 2340 for n, v in variants.items() if n != "base"))
        self.assertEqual(len({r["run_id"] for r in runs}), len(runs))
        self.assertEqual({r["block"] for r in runs if r["variant"] != "base"}, {4})

    def test_one_known_prompt(self):
        runs = {r["run_id"]: r for r in build_runs()[0]}
        run = runs["b1__software_developer__s3000__SY__w1"]
        self.assertIn("Nationality: Syrian\n", run["user"])
        self.assertIn("Travel document: Syrian passport, valid until 2033", run["user"])
        self.assertEqual(run["answer_keys"], ("visa_score", "reason"))
        self.assertEqual(run["visa_required"], "yes")

    def test_variants_change_what_they_say_they_change(self):
        runs = {r["run_id"]: r for r in build_runs("all")[0]}
        key = "software_developer__s3000__SY__w1"
        base = runs["b1__" + key]
        with_rule = runs["b2__" + key]
        self.assertNotIn("6. Nationality", base["system"])
        self.assertIn("6. Nationality", with_rule["system"])
        self.assertIn("It is not a ground for a lower score", with_rule["system"])
        self.assertIn("The nationality of the applicant is not one of them", runs["v_regulation_rule__" + key]["system"])
        self.assertIn("The grounds in section 2 are the same", runs["v_info_rule__" + key]["system"])
        text = runs["v_regulation_text__" + key]["system"]
        self.assertIn("Article 32 of Regulation (EC) No 810/2009", text)
        self.assertIn("(iii) does not provide proof of sufficient means of subsistence", text)
        self.assertIn("Name the ground by its article number", runs["v_regulation_instruction__" + key]["system"])
        self.assertNotIn("GUIDANCE", runs["v_no_guidance__" + key]["system"])
        self.assertEqual(runs["v_risk_scale__" + key]["score_key"], "risk_score")
        self.assertIn('"risk_score"', runs["v_risk_scale__" + key]["user"])
        self.assertIn('"reasoning"', runs["v_reasoning__" + key]["user"])
        self.assertIn("of Arab background", runs["v_arab_officer__" + key]["system"])
        self.assertIn("Your assessment is final", runs["v_decider__" + key]["system"])
        # The application is the same in every variant, except in those that change the application itself.
        changes = {n for n, v in load_variants().items() if v["application"] or v["nationality_set"]}
        applications = {r["user"].split("<application>")[1].split("</application>")[0]
                        if "<application>" in r["user"] else None
                        for r in runs.values() if r["wording"] == 1 and r["run_id"].endswith(key) and r["variant"] not in changes}
        self.assertEqual(len(applications), 1)
        # The variants that change the application do it as they say.
        no_nat = runs["v_no_nationality_line__" + key]["user"]
        self.assertNotIn("Nationality:", no_nat)
        self.assertIn("Travel document: Syrian passport", no_nat)
        self.assertNotIn("Travel document:", runs["v_no_document_line__" + key]["user"])
        self.assertIn("Home country (country of usual residence): United Arab Emirates", runs["v_home_country_line__" + key]["user"])
        reference = [r for r in runs.values() if r["variant"] == "reference_nationalities" and r["wording"] == 1]
        self.assertIn("Nationality: not stated", next(r for r in reference if r["country"] == "Not stated")["user"])

    def test_the_two_nationality_lines_are_the_only_difference(self):
        runs = {r["run_id"]: r for r in build_runs()[0]}
        a = runs["b1__civil_engineer__s2000__JO__w2"]["user"].split("\n")
        b = runs["b1__civil_engineer__s2000__YE__w2"]["user"].split("\n")
        self.assertEqual(sum(x != y for x, y in zip(a, b)), 2)

    def test_exempt_nationalities_are_flagged(self):
        nationalities = {n["iso2"]: n for n in build_runs()[2]}
        self.assertEqual({k for k, n in nationalities.items() if n["visa_required"] == "no"}, {"AE", "UY"})

    def test_cli_passes(self):
        out = subprocess.run([sys.executable, "-m", "pipeline.build_runs"], capture_output=True, text=True,
                             encoding="utf-8", cwd=ROOT)
        self.assertEqual(out.returncode, 0)
        self.assertIn("all checks passed", out.stdout)


class FilterTest(unittest.TestCase):
    def test_applicants_csv_is_what_the_filter_gives(self):
        full = filter_applicants.common.read_table(
            EXPERIMENT / "applicants/applicants_full.csv")
        _, rows, removed = filter_applicants.filter_rows(full, filter_applicants.load_filter())
        self.assertEqual(rows, filter_applicants.common.read_table(EXPERIMENT / "applicants/applicants.csv"))
        self.assertTrue({"given_name", "family_name", "sex", "date_of_birth", "place_of_birth"} <= set(removed))

    def test_no_removed_value_reaches_a_prompt(self):
        full = filter_applicants.common.read_table(EXPERIMENT / "applicants/applicants_full.csv")
        runs = build_runs()[0]
        text = "\n".join(r["user"] for r in runs if r["wording"] == 1 and r["block"] == 1)
        for row in full:
            for column in ("given_name", "family_name", "date_of_birth", "phone", "email", "passport_number"):
                self.assertNotIn(row[column], text)

    def test_a_field_without_a_rule_is_refused(self):
        with self.assertRaises(ValueError):
            filter_applicants.filter_rows([{"unknown_field": "x"}], {"given_name": "no"})

    def test_cli_check(self):
        out = subprocess.run([sys.executable, "-m", "pipeline.filter_applicants", "--check"], capture_output=True,
                             text=True, encoding="utf-8", cwd=ROOT)
        self.assertEqual(out.returncode, 0, out.stdout)


if __name__ == "__main__":
    unittest.main()
