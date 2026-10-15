"""Synthetic checker controls; these fixtures are not June candidate keys."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "verify_candidate.py"
SPEC = importlib.util.spec_from_file_location("verify_candidate", SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class CandidateVerificationTests(unittest.TestCase):
    def assert_rejected(self, error, text="baba", mapping=None, **kwargs):
        with self.assertRaises(CHECKER.VerificationError) as caught:
            CHECKER.verify_candidate(text, {"ba": "00"} if mapping is None else mapping, **kwargs)
        self.assertEqual(caught.exception.code, error)

    def test_synthetic_positive_preserves_null_case_words_and_whitespace(self):
        text = " \tBaumBa\nci\t dy  baba\r\n"
        result = CHECKER.verify_candidate(text, {"ba": "00", "ci": "17", "dy": "25"}, accept_vc_nulls=True)
        self.assertEqual(result["numeric_values"], ["0000", "1725", "0000"])
        self.assertEqual(result["reencrypted_text"], text)
        self.assertEqual(result["candidate_null_locations"][0]["source_span"], [4, 6])
        self.assertEqual(result["candidate_null_locations"][0]["text"], "um")
        self.assertTrue(result["codes"][1]["crosses_word_boundary"])
        self.assertEqual("".join(p["text"] for p in result["layout"]), text)
        self.assertEqual(result["input_sha256"], hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(result["input_sha256"], result["reencrypted_sha256"])
        self.assertEqual(result["validation_level"], "conditional_mechanical_consistency_only")
        self.assertFalse(result["historical_authentication"])
        self.assertFalse(result["independent_validation"])

    def test_missing_mapping(self):
        self.assert_rejected("missing_mapping", "babacidy")

    def test_noninjective_even_for_unused_entry(self):
        self.assert_rejected("noninjective_mapping", mapping={"ba": "00", "ci": "00"})

    def test_illegal_characters_cannot_resynchronize_into_success(self):
        for text in ("!baba", "baba7", "baba#cidy", "eeabab"):
            with self.subTest(text=text):
                self.assert_rejected("unresolved_input", text)

    def test_source_annotations_not_expanded(self):
        self.assert_rejected("unresolved_input", "baba(y)")

    def test_trailing_character(self):
        self.assert_rejected("unresolved_input", "babae")

    def test_trailing_syllable(self):
        self.assert_rejected("incomplete_code", "babaci")

    def test_odd_word_syllables_pair_across_word_boundaries(self):
        result = CHECKER.verify_candidate("ba ba", {"ba": "00"})
        self.assertTrue(result["codes"][0]["crosses_word_boundary"])
        self.assertEqual(result["reencrypted_text"], "ba ba")

    def test_nulls_require_explicit_hypothesis(self):
        self.assert_rejected("null_acceptance_required", "baumba")

    def test_empty_and_null_only_are_not_vacuous_passes(self):
        for text in ("", " \t\n", "um"):
            with self.subTest(text=text):
                self.assert_rejected("empty_ciphertext", text, accept_vc_nulls=True)

    def test_value_domain_is_exact_ascii_string(self):
        for value in (0, True, "0", "100", "-1", "１2", " 0", None):
            with self.subTest(value=value):
                self.assert_rejected("invalid_value", mapping={"ba": value})

    def test_mapping_keys_are_exactly_one_cv_syllable(self):
        for key in ("Ba", "baba", "b", "ab", "ee", "bā", "Ka"):
            with self.subTest(key=key):
                self.assert_rejected("invalid_code", mapping={key: "00"})

    def test_unicode_case_equivalents_are_not_promoted_to_ascii(self):
        self.assert_rejected("non_ascii_cipher_character", "Kaba", mapping={"ka": "00", "ba": "01"})

    def test_duplicate_json_key_is_rejected(self):
        for data in (b'{"ba":"00","ba":"17"}', b'{"ba":"00","ba":"00"}'):
            with self.subTest(data=data), self.assertRaises(CHECKER.VerificationError) as caught:
                CHECKER.load_mapping(data)
            self.assertEqual(caught.exception.code, "duplicate_mapping_key")

    def test_json_top_level_must_be_nonempty_object(self):
        for data in (b"{}", b"[]", b"null", b"1"):
            with self.subTest(data=data), self.assertRaises(CHECKER.VerificationError) as caught:
                CHECKER.load_mapping(data)
            self.assertEqual(caught.exception.code, "invalid_mapping")

    def test_round18_requires_explicit_acceptance(self):
        self.assert_rejected("emendation_acceptance_required", reading_id="R18_D:1917-06-24_0509")
        with self.assertRaises(CHECKER.VerificationError) as caught:
            CHECKER.select_reading("R18_B:1917-06-24_0509")
        self.assertEqual(caught.exception.code, "emendation_acceptance_required")
        selected, sources = CHECKER.select_reading("R18_B:1917-06-24_0509", accept_round18_emendations=True)
        self.assertIn("emended", selected["provenance"])
        self.assertTrue(all(len(s["sha256"]) == 64 for s in sources.values()))

    def test_declared_cleartext_signature_is_layout_only(self):
        result = CHECKER.verify_candidate("baba Tai\n", {"ba": "00"}, signature="Tai")
        self.assertEqual(result["numeric_values"], ["0000"])
        self.assertEqual(result["reencrypted_text"], "baba Tai\n")
        self.assertEqual([p["text"] for p in result["layout"] if p["kind"] == "signature"], ["Tai"])

    def test_unused_codes_disclosed_without_requiring_fictitious_full_table(self):
        result = CHECKER.verify_candidate("baba", {"ba": "00", "ci": "17", "dy": "25"})
        self.assertEqual(result["unused_mapping_syllables"], ["ci", "dy"])
        self.assertEqual(result["mapping_entries"], 3)
        self.assertEqual(result["observed_unique_codes"], 1)

    def test_one_syllable_table_reused_in_different_four_digit_codes(self):
        result = CHECKER.verify_candidate("mupo mumu popo", {"mu": "12", "po": "34"})
        self.assertEqual(result["numeric_values"], ["1234", "1212", "3434"])
        self.assertEqual(result["codes"][0]["syllable_values"], ["12", "34"])
        self.assertEqual(result["observed_unique_syllables"], 2)
        self.assertEqual(result["observed_unique_codes"], 3)
        self.assertEqual(result["reencrypted_text"], "mupo mumu popo")

    def test_all_null_positions_are_preserved(self):
        text = "umBaumba abci dyum"
        result = CHECKER.verify_candidate(text, {"ba": "00", "ci": "17", "dy": "25"}, accept_vc_nulls=True)
        self.assertEqual([t["text"] for t in result["candidate_null_locations"]], ["um", "um", "ab", "um"])
        self.assertEqual(result["numeric_values"], ["0000", "1725"])
        self.assertEqual(result["reencrypted_text"], text)


class CommandLineTests(unittest.TestCase):
    def test_cli_from_unrelated_cwd_and_raw_file_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            mapping = directory / "mapping.json"
            ciphertext = directory / "cipher.txt"
            table_bytes = b'{ "ba": "00" }\n'
            text_bytes = b"Ba Ba\r\n"
            mapping.write_bytes(table_bytes)
            ciphertext.write_bytes(text_bytes)
            run = subprocess.run([sys.executable, str(SCRIPT), "--mapping", str(mapping), "--text-file", str(ciphertext)], cwd=tmp, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            result = json.loads(run.stdout)
            self.assertEqual(result["reencrypted_text"].encode(), text_bytes)
            self.assertEqual(result["mapping_file_sha256"], hashlib.sha256(table_bytes).hexdigest())
            self.assertEqual(result["input_file_sha256"], hashlib.sha256(text_bytes).hexdigest())
            self.assertEqual(result["input_sha256"], result["input_file_sha256"])

    def test_cli_failure_is_json_with_nonzero_exit_and_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            mapping = directory / "mapping.json"
            ciphertext = directory / "cipher.txt"
            mapping.write_text('{"ba":"00"}', encoding="utf-8")
            ciphertext.write_text("babaci", encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), "--mapping", str(mapping), "--text-file", str(ciphertext)], cwd=tmp, capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            result = json.loads(run.stdout)
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["error"]["code"], "incomplete_code")
            self.assertIn("input_sha256", result)
            self.assertIn("mapping_file_sha256", result)


if __name__ == "__main__":
    unittest.main()
