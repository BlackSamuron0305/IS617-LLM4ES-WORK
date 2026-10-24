"""Tests for the judge_build stage. No real model is called: the answers come from the mock
client or are written to the processed table by hand."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from pipeline import build_runs, client, judge_build
from pipeline.client import JUDGE_MARKER, MockClient
from pipeline.common import EXPERIMENT, read_jsonl, read_table, read_text, sha256_text, write_csv
from pipeline.judge_build import (JUDGE, JUDGE_CODES, build_judge_items, compile_masker, main, mask,
                                  masking_terms)
from pipeline.parse_answers import ANSWER_COLUMNS, parse_batch
from pipeline.run_models import run_answers

NATS = read_table(EXPERIMENT / "countries/applicant_nationalities.csv")
ROWS = read_table(JUDGE / "mask_terms.csv")
APPLICANTS = read_table(EXPERIMENT / "applicants/applicants.csv")
UAE = "United Arab Emirates"


def masker_for(country):
    return compile_masker(masking_terms(NATS, ROWS, next(n for n in NATS if n["country"] == country)))


def answer_row(**fields):
    # One row of processed/<batch>/answers.csv; what the test does not set is blank.
    applicant = APPLICANTS[0]
    row = dict.fromkeys(ANSWER_COLUMNS, "")
    row.update(applicant_id=applicant["applicant_id"], savings=applicant["savings"], country="Syria",
               parse_status="ok", reason="The stay is short.", repetition="0")
    row.update(fields)
    return row


def run_quietly(function, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return function(*args, **kwargs)


class MaskingTest(unittest.TestCase):
    def test_masks_own_and_other_nationalities(self):
        self.assertEqual(mask("The applicant holds a Syrian passport and Syria is at war.", masker_for("Syria")),
                         ("The applicant holds a [NATIONALITY] passport and [PASSPORT COUNTRY] is at war.", 2))

    def test_keeps_residence_terms_for_non_emirati(self):
        text = "As a non-Emirati resident of the United Arab Emirates, the status depends on the job."
        self.assertEqual(mask(text, masker_for("Syria")), (text, 0))

    def test_masks_emirati_for_emirati_applicant_only(self):
        self.assertEqual(mask("An Emirati citizen living in the United Arab Emirates.", masker_for(UAE)),
                         ("An [NATIONALITY] citizen living in the United Arab Emirates.", 1))

    def test_plural_case_longest_first_regions_capitals(self):
        m = masker_for("Saudi Arabia")
        self.assertEqual(mask("SYRIANS and Saudi Arabian nationals from Saudi Arabia", m)[0],
                         "[NATIONALITY] and [NATIONALITY] nationals from [PASSPORT COUNTRY]")
        self.assertEqual(mask("unrest in the Middle East, Damascus", m)[0], "unrest in the [REGION], [PLACE]")
        self.assertEqual(mask("a woman in Amman", m)[0], "a woman in [PLACE]")
        self.assertEqual(mask("born in Muscat or Phnom Penh", masker_for("Oman")), ("born in [PLACE] or [PLACE]", 2))

    def test_aliases_and_longer_terms_win(self):
        m = masker_for("Palestine")
        self.assertEqual(mask("Palestinian territories and the West Bank", m),
                         ("[PASSPORT COUNTRY] and the [PASSPORT COUNTRY]", 2))
        self.assertEqual(mask("the Kingdom of Saudi Arabia, KSA", m)[0], "the [PASSPORT COUNTRY], [PASSPORT COUNTRY]")
        self.assertEqual(mask("Kuwait City is not Kuwait", m)[0], "[PLACE] is not [PASSPORT COUNTRY]")

    def test_word_boundaries_leave_other_words_alone(self):
        m = masker_for("Syria")
        text = "Arabic documents, a male clerk, Omanis and Africans"
        self.assertEqual(mask(text, m)[0], "Arabic documents, a male clerk, [NATIONALITY] and [REGION]")

    def test_every_nationality_is_hidden_for_every_applicant(self):
        for own in NATS:
            m = masker_for(own["country"])
            for other in NATS:
                if other["country"] == UAE and own["country"] != UAE:
                    continue  # the country of residence stays visible; the demonym of an Emirati applicant only
                text = mask(f"A {other['demonym']} passport, {other['country']}.", m)[0]
                self.assertNotIn(other["demonym"], text, (own["country"], other["country"]))
                if other["country"] != UAE:
                    self.assertNotIn(other["country"], text, (own["country"], other["country"]))

    def test_known_leak_uae_citizen_stays_unmasked(self):
        # Documented in experiment/judge/README.md: only the words in mask_terms.csv are masked.
        self.assertEqual(mask("A UAE citizen.", masker_for(UAE)), ("A UAE citizen.", 0))

    def test_mask_terms_file_shape(self):
        self.assertEqual(list(ROWS[0]), ["term", "replacement", "kind"])
        self.assertEqual({row["kind"] for row in ROWS}, {"alias", "capital", "region", "keep"})
        for row in ROWS:
            self.assertEqual(row["replacement"] == "", row["kind"] == "keep", row)
        self.assertEqual({row["term"] for row in ROWS if row["kind"] == "keep"},
                         {"United Arab Emirates", "Emirati", "Abu Dhabi"})

    def test_unknown_kind_is_refused(self):
        with self.assertRaises(ValueError):
            masking_terms(NATS, [{"term": "x", "replacement": "[X]", "kind": "other"}], NATS[0])


class MaterialsTest(unittest.TestCase):
    def test_judge_task_placeholders_and_codes(self):
        task, prompt = read_text(JUDGE / "judge_task.txt"), read_text(JUDGE / "judge_prompt.txt")
        self.assertEqual((task.count("{application}"), task.count("{reason}")), (1, 1))
        for code in JUDGE_CODES:
            self.assertIn(f'"{code}"', task)
            self.assertIn(f"{code}:", prompt)

    def test_client_marker_is_the_marker_line_of_the_task(self):
        self.assertIn(JUDGE_MARKER, read_text(JUDGE / "judge_task.txt").splitlines())

    def test_client_uses_the_shared_constants(self):
        self.assertIs(client.JUDGE_CODES, judge_build.JUDGE_CODES)
        self.assertIs(client.CHECK_LETTERS, build_runs.CHECK_LETTERS)

    def test_judge_models_file(self):
        models = read_table(JUDGE / "judge_models.csv")
        self.assertEqual([m["role"] for m in models], ["primary", "agreement_check"])
        self.assertEqual([m["alias"] for m in models], ["gpt-oss-120b", "qwen3-32b"])


class BuildItemsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def write_answers(self, batch, rows):
        write_csv(self.tmp / "processed" / batch / "answers.csv", rows, ANSWER_COLUMNS)

    def test_build_items_end_to_end(self):
        run_quietly(run_answers, "mock_j", "qwen3-8b", MockClient("answers"), self.tmp, blocks=[1], limit=60,
                    mock=True)
        run_quietly(parse_batch, "mock_j", self.tmp)
        summary = build_judge_items("mock_j", self.tmp)
        items = read_jsonl(self.tmp / "processed/mock_j/judge_items.jsonl")
        self.assertEqual(summary["items"], len(items))
        self.assertLess(len(items), summary["linked"])  # identical masked inputs collapse
        for item in items:
            for n in NATS:
                self.assertNotIn(n["demonym"], item["user"])  # no nationality reaches the judge
            for field in ("risk_score", "risk_rating", "recommendation"):
                self.assertNotIn(field, item["user"])  # the judge never sees the verdict
            self.assertEqual(item["item_id"], sha256_text(item["system"] + "\n" + item["user"])[:16])
            self.assertEqual(item["system"], read_text(JUDGE / "judge_prompt.txt"))
            self.assertIn(item["reason_masked"], item["user"])
        self.assertEqual(len({item["item_id"] for item in items}), len(items))
        links = read_table(self.tmp / "processed/mock_j/judge_links.csv")
        self.assertEqual(list(links[0]), ["key", "run_id", "repetition", "item_id", "n_masked"])
        self.assertEqual(len(links), summary["linked"])
        self.assertEqual(summary["answers"], summary["linked"] + summary["skipped"])
        self.assertLessEqual({link["item_id"] for link in links}, {item["item_id"] for item in items})
        # The mock answers name the nationality in some reasons; those were masked.
        masked = [link for link in links if int(link["n_masked"]) > 0]
        self.assertTrue(masked)
        by_id = {item["item_id"]: item for item in items}
        for link in masked:
            self.assertIn("[NATIONALITY]", by_id[link["item_id"]]["reason_masked"])

    def test_application_shown_to_the_judge_has_the_placeholder(self):
        self.write_answers("mock_a", [answer_row(key="k1", run_id="r1", country="Egypt")])
        build_judge_items("mock_a", self.tmp)
        user = read_jsonl(self.tmp / "processed/mock_a/judge_items.jsonl")[0]["user"]
        self.assertIn("Nationality: [NATIONALITY]\n", user)
        self.assertIn("Travel document: [NATIONALITY] passport, valid until 2033\n", user)
        self.assertIn(f"Savings: AED {APPLICANTS[0]['savings']} ", user)
        self.assertNotIn("{", user)

    def test_skips_failed_and_empty_reasons(self):
        self.write_answers("mock_k", [answer_row(key="k1", run_id="r1"),
                                      answer_row(key="k2", run_id="r2", parse_status="no_json", reason=""),
                                      answer_row(key="k3", run_id="r3", reason="  ")])
        summary = build_judge_items("mock_k", self.tmp)
        self.assertEqual(summary, {"answers": 3, "linked": 1, "items": 1, "skipped": 2})

    def test_same_reason_and_application_give_one_item_for_many_nationalities(self):
        rows = [answer_row(key=f"k{i}", run_id=f"r{i}", country=country, reason=f"A {demonym} applicant.")
                for i, (country, demonym) in enumerate([("Syria", "Syrian"), ("Egypt", "Egyptian"),
                                                        ("Syria", "Syrians")])]
        self.write_answers("mock_d", rows)
        summary = build_judge_items("mock_d", self.tmp)
        self.assertEqual((summary["linked"], summary["items"]), (3, 1))
        links = read_table(self.tmp / "processed/mock_d/judge_links.csv")
        self.assertEqual(len({link["item_id"] for link in links}), 1)
        self.assertEqual([link["n_masked"] for link in links], ["1", "1", "1"])

    def test_rows_are_rewritten_not_appended_and_keep_first_seen_order(self):
        rows = [answer_row(key="k1", run_id="r1", reason="First reason."),
                answer_row(key="k2", run_id="r2", reason="Second reason.")]
        self.write_answers("mock_r", rows)
        build_judge_items("mock_r", self.tmp)
        build_judge_items("mock_r", self.tmp)
        items = read_jsonl(self.tmp / "processed/mock_r/judge_items.jsonl")
        self.assertEqual([item["reason_masked"] for item in items], ["First reason.", "Second reason."])
        self.assertEqual(len(read_table(self.tmp / "processed/mock_r/judge_links.csv")), 2)

    def test_main_without_answers_returns_2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(main(["--batch", "mock_none", "--data-root", str(self.tmp)]), 2)
        self.assertIn("mock_none", err.getvalue())

    def test_main_runs(self):
        self.write_answers("mock_m", [answer_row(key="k1", run_id="r1")])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["--batch", "mock_m", "--data-root", str(self.tmp)]), 0)
        self.assertIn("1 unique", out.getvalue())


if __name__ == "__main__":
    unittest.main()
