"""Tests for the judge_validate stage: the sample for hand-coding and the agreement with the judge.
No model is called; every file is built by hand in a temporary folder."""

import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path

from pipeline.client import JUDGE_MARKER
from pipeline.common import read_text, write_csv
from pipeline.judge_build import JUDGE, JUDGE_CODES, write_jsonl
from pipeline.judge_parse import JUDGE_CODE_COLUMNS
from pipeline.judge_validate import KAPPA_MIN, agreement, cohen_kappa, draw_sample, main, read_codes

HUMAN_COLUMNS = ["item_id", *JUDGE_CODES, "coder", "note"]
TASK = read_text(JUDGE / "judge_task.txt")


def run_cli(argv):
    with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def read_rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def judge_user(k, reason):
    # The judge's user message: the real judge_task.txt around a masked application, so that the
    # test breaks if the layout of that file changes.
    application = (f"Application reference: R{k:04d}\nLodged: online\n\nAPPLICANT\nNationality: [NATIONALITY]\n"
                   "Travel document: [NATIONALITY] passport, valid until 2033\n\nSavings: AED 16,000")
    return TASK.replace("{application}", application).replace("{reason}", reason)


def write_items(data_root, batch, masked, plain):
    # judge_items.jsonl with `masked` items that had a nationality word hidden and `plain` that had none.
    items = [{"item_id": f"m{k:03d}", "applicant_id": "A01", "reason_masked": f"masked reason {k}", "n_masked": 1,
              "system": "s", "user": judge_user(k, f"masked reason {k}")} for k in range(masked)]
    items += [{"item_id": f"p{k:03d}", "applicant_id": "A02", "reason_masked": f"plain reason {k}", "n_masked": 0,
               "system": "s", "user": judge_user(1000 + k, f"plain reason {k}")} for k in range(plain)]
    folder = Path(data_root) / "processed" / batch
    folder.mkdir(parents=True, exist_ok=True)
    write_jsonl(folder / "judge_items.jsonl", items)
    return items


def write_judge_codes(data_root, batch, alias, rows):
    # rows: item_id -> (judge_status, {code: 1/0}); codes not given stay blank.
    table = [{"item_id": item_id, "applicant_id": "A01", "n_masked": 0, "reason_masked": "r",
              "judge_status": status, **codes, "evidence": ""} for item_id, (status, codes) in rows.items()]
    path = Path(data_root) / "processed" / batch / f"judge_codes_{alias}.csv"
    write_csv(path, table, JUDGE_CODE_COLUMNS)
    return path


def write_human(path, rows):
    # rows: item_id -> {code: "yes"/"no"/...}; codes not given stay blank.
    write_csv(path, [{"item_id": item_id, **codes} for item_id, codes in rows.items()], HUMAN_COLUMNS)
    return path


class KappaTest(unittest.TestCase):
    def test_kappa(self):
        self.assertEqual(cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]), 1.0)
        self.assertEqual(cohen_kappa([1, 1, 0, 0], [1, 0, 1, 0]), 0.0)
        self.assertEqual(cohen_kappa([1, 1, 1, 0], [1, 1, 0, 0]), 0.5)
        self.assertIsNone(cohen_kappa([1, 1, 1], [1, 1, 1]))

    def test_kappa_all_zero_is_none_too(self):
        self.assertIsNone(cohen_kappa([0, 0], [0, 0]))

    def test_kappa_can_be_negative(self):
        self.assertEqual(cohen_kappa([1, 0, 1, 0], [0, 1, 0, 1]), -1.0)

    def test_kappa_one_sided_constant_is_zero(self):
        # One coder says 1 everywhere: whatever the other says, the agreement is what chance gives.
        self.assertEqual(cohen_kappa([1, 1, 1, 1], [1, 1, 0, 0]), 0.0)

    def test_kappa_empty_or_unequal_lists_raise(self):
        with self.assertRaises(ValueError):
            cohen_kappa([], [])
        with self.assertRaises(ValueError):
            cohen_kappa([1, 0], [1])


class AgreementTest(unittest.TestCase):
    def test_agreement_passes_flag(self):
        a = {f"i{k}": {c: k % 2 for c in JUDGE_CODES} for k in range(10)}
        rows = {r["code"]: r for r in agreement(a, a)}
        self.assertTrue(rows["doubts_residence"]["passes"])
        self.assertEqual(rows["doubts_residence"]["n"], 10)
        self.assertEqual(list(rows), list(JUDGE_CODES))
        self.assertEqual(set(rows["doubts_residence"]), {"code", "n", "agree_share", "kappa", "passes"})
        self.assertEqual((rows["doubts_residence"]["agree_share"], rows["doubts_residence"]["kappa"]), (1.0, 1.0))

    def test_threshold_is_provisional_seven_tenths(self):
        self.assertEqual(KAPPA_MIN, 0.7)

    def test_below_threshold_does_not_pass(self):
        a = {f"i{k}": dict.fromkeys(JUDGE_CODES, k % 2) for k in range(4)}
        b = {f"i{k}": dict.fromkeys(JUDGE_CODES, (k // 2) % 2) for k in range(4)}  # 1,1,0,0 against 0,1,0,1
        row = agreement(a, b)[0]
        self.assertEqual((row["n"], row["agree_share"], row["kappa"], row["passes"]), (4, 0.5, 0.0, False))

    def test_only_items_with_a_value_on_both_sides_count(self):
        a = {"i0": {"mentions_nationality": 1}, "i1": {"mentions_nationality": 0}, "i2": {"mentions_nationality": 1},
             "only_a": {"mentions_nationality": 1}}
        b = {"i0": {"mentions_nationality": 1}, "i1": {"mentions_nationality": 0}, "i2": {},
             "only_b": {"mentions_nationality": 0}}
        rows = {r["code"]: r for r in agreement(a, b)}
        self.assertEqual(rows["mentions_nationality"]["n"], 2)
        self.assertEqual(rows["mentions_nationality"]["kappa"], 1.0)
        # No item has a value for the other codes on either side.
        self.assertEqual(rows["doubts_residence"]["n"], 0)

    def test_no_items_gives_none_and_does_not_pass(self):
        row = agreement({}, {})[0]
        self.assertEqual((row["n"], row["agree_share"], row["kappa"], row["passes"]), (0, None, None, False))

    def test_constant_codes_give_no_kappa_and_do_not_pass(self):
        a = {f"i{k}": dict.fromkeys(JUDGE_CODES, 0) for k in range(5)}
        row = agreement(a, a)[0]
        self.assertEqual((row["n"], row["agree_share"], row["kappa"], row["passes"]), (5, 1.0, None, False))


class ReadCodesTest(unittest.TestCase):
    def test_yes_no_one_zero_and_blank(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_human(Path(tmp) / "h.csv", {
                "a": {"mentions_nationality": "yes", "nationality_as_risk": "No", "doubts_residence": " YES "},
                "b": {"mentions_nationality": "1", "nationality_as_risk": "0"},
                "blank": {}})
            codes = read_codes(path)
        self.assertEqual(codes, {"a": {"mentions_nationality": 1, "nationality_as_risk": 0, "doubts_residence": 1},
                                 "b": {"mentions_nationality": 1, "nationality_as_risk": 0}})

    def test_judge_file_counts_ok_and_inconsistent_rows_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            all_one = dict.fromkeys(JUDGE_CODES, 1)
            path = write_judge_codes(tmp, "b", "j", {
                "ok": ("ok", all_one), "inc": ("inconsistent", all_one), "bad": ("bad_value", {}),
                "none": ("no_json", {}), "late": ("not_run", {}), "err": ("call_error", {})})
            codes = read_codes(path)
        self.assertEqual(set(codes), {"ok", "inc"})
        self.assertEqual(codes["ok"], all_one)

    def test_judge_status_filter_beats_filled_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_judge_codes(tmp, "b", "j", {"x": ("bad_value", dict.fromkeys(JUDGE_CODES, 1))})
            self.assertEqual(read_codes(path), {})

    def test_unknown_value_is_an_error_that_names_the_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_human(Path(tmp) / "h.csv", {"it7": {"doubts_residence": "maybe"}})
            with self.assertRaises(ValueError) as caught:
                read_codes(path)
        self.assertIn("it7", str(caught.exception))
        self.assertIn("doubts_residence", str(caught.exception))

    def test_file_without_item_id_column_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "h.csv"
            path.write_text("id;mentions_nationality\na;yes\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_codes(path)

    def test_byte_order_mark_from_a_spreadsheet_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "h.csv"
            path.write_text("item_id,mentions_nationality\na,yes\n", encoding="utf-8-sig")
            self.assertEqual(read_codes(path), {"a": {"mentions_nationality": 1}})


class SampleTest(unittest.TestCase):
    def test_sample_oversamples_masked_and_hides_judge(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            items = write_items(tmp, "mock_v", masked=10, plain=90)
            masked_ids = {i["item_id"] for i in items if i["n_masked"] > 0}
            path = draw_sample("mock_v", 20, 617, tmp)
            self.assertEqual(path, tmp / "processed/mock_v/validation_sample.csv")
            first_text = path.read_text(encoding="utf-8")
            rows = read_rows(path)
            self.assertEqual(len(rows), 20)
            self.assertEqual(sum(1 for r in rows if r["item_id"] in masked_ids), 10)
            self.assertTrue(all(r["mentions_nationality"] == "" for r in rows))
            self.assertEqual(draw_sample("mock_v", 20, 617, tmp, force=True).read_text(encoding="utf-8"),
                             first_text)  # same seed, same sample

    def test_columns_and_blank_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_items(tmp, "mock_v", masked=3, plain=3)
            rows = read_rows(draw_sample("mock_v", 4, 1, tmp))
        self.assertEqual(list(rows[0]), ["item_id", "applicant_id", "reason_masked", "application_masked",
                                         *JUDGE_CODES, "coder", "note"])
        for row in rows:
            self.assertRegex(row["reason_masked"], r"^(masked|plain) reason \d$")
            self.assertEqual(row["applicant_id"], "A01" if row["item_id"].startswith("m") else "A02")
            for column in [*JUDGE_CODES, "coder", "note"]:
                self.assertEqual(row[column], "")

    def test_sample_does_not_contain_judge_codes_even_when_a_judge_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_items(tmp, "mock_v", masked=2, plain=2)
            write_judge_codes(tmp, "mock_v", "j", {k: ("ok", dict.fromkeys(JUDGE_CODES, 1)) for k in
                                                   ("m000", "m001", "p000", "p001")})
            rows = read_rows(draw_sample("mock_v", 4, 1, tmp))
        self.assertTrue(all(r[code] == "" for r in rows for code in JUDGE_CODES))
        self.assertNotIn("judge_status", rows[0])
        self.assertNotIn("evidence", rows[0])

    def test_same_seed_same_sample_whatever_the_file_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            items = write_items(tmp, "mock_v", masked=10, plain=90)
            first = draw_sample("mock_v", 20, 617, tmp).read_bytes()
            write_jsonl(tmp / "processed/mock_v/judge_items.jsonl", list(reversed(items)))
            self.assertEqual(draw_sample("mock_v", 20, 617, tmp, force=True).read_bytes(), first)

    def test_another_seed_gives_another_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_items(tmp, "mock_v", masked=10, plain=90)
            one = draw_sample("mock_v", 20, 1, tmp).read_bytes()
            two = draw_sample("mock_v", 20, 2, tmp, force=True).read_bytes()
        self.assertNotEqual(one, two)

    def test_few_masked_items_are_all_taken_and_the_rest_filled_from_the_others(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_items(tmp, "mock_v", masked=3, plain=90)
            rows = read_rows(draw_sample("mock_v", 20, 617, tmp))
        self.assertEqual(len(rows), 20)
        self.assertEqual(sum(1 for r in rows if r["item_id"].startswith("m")), 3)

    def test_few_plain_items_are_all_taken_and_the_rest_filled_from_the_masked(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_items(tmp, "mock_v", masked=50, plain=2)
            rows = read_rows(draw_sample("mock_v", 20, 617, tmp))
        self.assertEqual(len(rows), 20)
        self.assertEqual(sum(1 for r in rows if r["item_id"].startswith("p")), 2)
        self.assertEqual(len({r["item_id"] for r in rows}), 20)

    def test_n_larger_than_the_items_takes_all_of_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_items(tmp, "mock_v", masked=4, plain=6)
            rows = read_rows(draw_sample("mock_v", 200, 617, tmp))
        self.assertEqual(sorted(r["item_id"] for r in rows), sorted([f"m{k:03d}" for k in range(4)] +
                                                                    [f"p{k:03d}" for k in range(6)]))

    def test_odd_n_gives_the_extra_item_to_the_unmasked_pool(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_items(tmp, "mock_v", masked=10, plain=90)
            rows = read_rows(draw_sample("mock_v", 21, 617, tmp))
        self.assertEqual(sum(1 for r in rows if r["item_id"].startswith("m")), 10)
        self.assertEqual(len(rows), 21)

    def test_sample_is_shuffled(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_items(tmp, "mock_v", masked=10, plain=90)
            ids = [r["item_id"] for r in read_rows(draw_sample("mock_v", 20, 617, tmp))]
        # Masked items are not all at the front.
        self.assertNotEqual([i[0] for i in ids], sorted(i[0] for i in ids))

    def test_application_is_shown_as_the_judge_saw_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            items = write_items(tmp, "mock_v", masked=3, plain=3)
            rows = read_rows(draw_sample("mock_v", 6, 617, tmp))
        users = {item["item_id"]: item["user"] for item in items}
        self.assertEqual(len(rows), 6)
        for row in rows:
            application = row["application_masked"]
            self.assertTrue(application.startswith("Application reference:"))
            self.assertIn("Nationality: [NATIONALITY]", application)
            self.assertNotIn("REASON GIVEN BY THE MODEL", application)
            self.assertNotIn(row["reason_masked"], application)
            self.assertEqual(application, application.strip("\n"))
            # Exactly the text between the line APPLICATION and the blank line before the reason marker.
            self.assertEqual(users[row["item_id"]].partition(JUDGE_MARKER)[0], "APPLICATION\n" + application + "\n\n")

    def test_input_without_the_judge_layout_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            items = write_items(tmp, "mock_v", masked=1, plain=0)
            items[0]["user"] = "u"
            write_jsonl(Path(tmp) / "processed/mock_v/judge_items.jsonl", items)
            with self.assertRaises(ValueError) as caught:
                draw_sample("mock_v", 1, 617, tmp)
            self.assertIn("m000", str(caught.exception))
            self.assertFalse((Path(tmp) / "processed/mock_v/validation_sample.csv").exists())

    def test_second_draw_without_force_raises_and_keeps_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_items(tmp, "mock_v", masked=10, plain=90)
            path = draw_sample("mock_v", 20, 617, tmp)
            # The hand-coder has been working in the file.
            coded = path.read_text(encoding="utf-8") + "hand-coding goes here\n"
            path.write_text(coded, encoding="utf-8")
            for seed in (617, 5):
                with self.assertRaises(FileExistsError) as caught:
                    draw_sample("mock_v", 20, seed, tmp)
                self.assertIn("--force", str(caught.exception))
                self.assertIn("copy", str(caught.exception))
                self.assertEqual(path.read_text(encoding="utf-8"), coded)
            draw_sample("mock_v", 20, 617, tmp, force=True)
            self.assertNotEqual(path.read_text(encoding="utf-8"), coded)

    def test_missing_items_file_and_bad_n(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                draw_sample("mock_v", 20, 617, tmp)
            write_items(tmp, "mock_v", masked=1, plain=1)
            with self.assertRaises(ValueError):
                draw_sample("mock_v", 0, 617, tmp)


class CliTest(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.tmp = Path(self._dir.name)
        # Four items; every code reads 1,0,1,0 for the human and, except where a test changes it, for the judge.
        pattern = {"i0": 1, "i1": 0, "i2": 1, "i3": 0}
        self.human = write_human(self.tmp / "human.csv", {
            i: {c: "yes" if v else "no" for c in JUDGE_CODES} for i, v in pattern.items()})
        self.pattern = pattern
        self.argv = ["agreement", "--batch", "mock_v", "--human", str(self.human), "--data-root", str(self.tmp)]

    def judge(self):
        # The judge agrees with the human on every code.
        rows = {i: ("ok", dict.fromkeys(JUDGE_CODES, v)) for i, v in self.pattern.items()}
        return write_judge_codes(self.tmp, "mock_v", "gpt-oss-120b", rows)

    def test_cli_agreement_writes_file(self):
        self.judge()
        code, out, err = run_cli([*self.argv, "--judge", "gpt-oss-120b"])
        self.assertEqual(code, 0)
        path = self.tmp / "processed/mock_v/validation_agreement_gpt-oss-120b.csv"
        self.assertTrue(path.exists())
        rows = read_rows(path)
        self.assertEqual([r["code"] for r in rows], list(JUDGE_CODES))
        self.assertEqual([(r["n"], r["agree_share"], r["kappa"], r["passes"]) for r in rows],
                         [("4", "1.0", "1.0", "True")] * 5)
        for code_name in JUDGE_CODES:
            self.assertIn(code_name, out)
        self.assertEqual(err, "")

    def test_none_is_an_empty_cell_and_n_a_in_the_table(self):
        # Both coders say no everywhere: they agree, but chance alone would give that, so there is no kappa.
        write_human(self.human, {i: {c: "no" for c in JUDGE_CODES} for i in self.pattern})
        write_judge_codes(self.tmp, "mock_v", "gpt-oss-120b",
                          {i: ("ok", dict.fromkeys(JUDGE_CODES, 0)) for i in self.pattern})
        code, out, _ = run_cli([*self.argv, "--judge", "gpt-oss-120b"])
        self.assertEqual(code, 0)
        rows = read_rows(self.tmp / "processed/mock_v/validation_agreement_gpt-oss-120b.csv")
        self.assertEqual((rows[0]["n"], rows[0]["agree_share"], rows[0]["kappa"], rows[0]["passes"]),
                         ("4", "1.0", "", "False"))
        self.assertIn("n/a", out)

    def test_no_overlap_prints_n_a_and_still_succeeds(self):
        write_judge_codes(self.tmp, "mock_v", "gpt-oss-120b",
                          {"other": ("ok", dict.fromkeys(JUDGE_CODES, 1))})
        code, out, _ = run_cli([*self.argv, "--judge", "gpt-oss-120b"])
        self.assertEqual(code, 0)
        rows = read_rows(self.tmp / "processed/mock_v/validation_agreement_gpt-oss-120b.csv")
        self.assertEqual([(r["n"], r["agree_share"], r["kappa"], r["passes"]) for r in rows],
                         [("0", "", "", "False")] * 5)
        self.assertIn("n/a", out)

    def test_other_human_file_is_named_by_its_stem(self):
        other = write_human(self.tmp / "second_coder.csv", {
            i: {c: "yes" if v else "no" for c in JUDGE_CODES} for i, v in self.pattern.items()})
        code, _, _ = run_cli([*self.argv, "--other-human", str(other)])
        self.assertEqual(code, 0)
        rows = read_rows(self.tmp / "processed/mock_v/validation_agreement_second_coder.csv")
        self.assertEqual(rows[0]["kappa"], "1.0")

    def test_missing_files_return_two_with_a_message(self):
        code, out, err = run_cli([*self.argv, "--judge", "gpt-oss-120b"])  # no judge file yet
        self.assertEqual(code, 2)
        self.assertIn("judge_codes_gpt-oss-120b.csv", err)
        self.judge()
        code, _, err = run_cli(["agreement", "--batch", "mock_v", "--human", str(self.tmp / "nope.csv"),
                                "--judge", "gpt-oss-120b", "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("nope.csv", err)
        code, _, err = run_cli([*self.argv, "--other-human", str(self.tmp / "nobody.csv")])
        self.assertEqual(code, 2)
        self.assertIn("nobody.csv", err)

    def test_unreadable_codes_return_two(self):
        write_human(self.human, {"i0": {"doubts_residence": "maybe"}})
        self.judge()
        code, _, err = run_cli([*self.argv, "--judge", "gpt-oss-120b"])
        self.assertEqual(code, 2)
        self.assertIn("maybe", err)

    def test_judge_or_other_human_is_required_and_exclusive(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(self.argv)
            with self.assertRaises(SystemExit):
                main([*self.argv, "--judge", "j", "--other-human", "x.csv"])

    def test_sample_subcommand_defaults_and_missing_input(self):
        code, _, err = run_cli(["sample", "--batch", "mock_v", "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("judge_items.jsonl", err)
        write_items(self.tmp, "mock_v", masked=100, plain=300)
        code, out, _ = run_cli(["sample", "--batch", "mock_v", "--data-root", str(self.tmp)])
        self.assertEqual(code, 0)
        path = self.tmp / "processed/mock_v/validation_sample.csv"
        rows = read_rows(path)
        self.assertEqual(len(rows), 200)  # --n defaults to 200
        self.assertEqual(sum(1 for r in rows if r["item_id"].startswith("m")), 100)
        self.assertIn(str(path), out)
        # --seed defaults to 617
        self.assertEqual(draw_sample("mock_v", 200, 617, self.tmp, force=True).read_bytes(), path.read_bytes())

    def test_sample_subcommand_refuses_to_overwrite_unless_forced(self):
        write_items(self.tmp, "mock_v", masked=5, plain=5)
        argv = ["sample", "--batch", "mock_v", "--n", "4", "--data-root", str(self.tmp)]
        self.assertEqual(run_cli(argv)[0], 0)
        path = self.tmp / "processed/mock_v/validation_sample.csv"
        path.write_text("my hand-coding\n", encoding="utf-8")
        code, out, err = run_cli(argv)
        self.assertEqual(code, 2)
        self.assertIn("--force", err)
        self.assertEqual(path.read_text(encoding="utf-8"), "my hand-coding\n")
        code, _, err = run_cli([*argv, "--force"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(len(read_rows(path)), 4)

    def test_sample_with_a_bad_n_returns_two(self):
        write_items(self.tmp, "mock_v", masked=1, plain=1)
        code, _, err = run_cli(["sample", "--batch", "mock_v", "--n", "0", "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertNotEqual(err, "")


if __name__ == "__main__":
    unittest.main()
