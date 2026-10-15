"""Character conservation and provenance regression tests (standard library)."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "provenance_audit.py"
SPEC = importlib.util.spec_from_file_location("provenance_audit", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class LosslessParserTests(unittest.TestCase):
    def test_y_has_two_roles(self):
        tokens = AUDIT.parse_word("yomyya")
        self.assertEqual([(t["kind"], t["text"]) for t in tokens], [("cv", "yo"), ("cv", "my"), ("cv", "ya")])
        self.assertEqual([t["cv_position_in_word"] for t in tokens], [0, 1, 2])

    def test_ee_never_disappears_and_um_is_only_candidate_null(self):
        tokens = AUDIT.parse_word("eeum")
        self.assertEqual([(t["kind"], t["text"]) for t in tokens], [("invalid_char", "e"), ("invalid_char", "e"), ("candidate_null", "um")])
        ee = AUDIT.parse_word("ee")
        self.assertEqual([t["kind"] for t in ee], ["invalid_char", "trailing_char"])

    def test_odd_words_keep_tail_and_do_not_get_a_code_count(self):
        reading = AUDIT.parse_reading("catyidohe")
        self.assertEqual(reading["words"][0]["tokens"][-1]["text"], "e")
        self.assertEqual(reading["summary"]["token_counts"]["trailing_char"], 1)
        self.assertIsNone(reading["summary"]["candidate_code_count"])

    def test_annotations_are_unresolved_not_expanded(self):
        reading = AUDIT.parse_reading("hutadyny(y)go mevecafema(u) rifyjabo(?)")
        self.assertEqual(reading["summary"]["token_counts"]["annotation"], 3)
        self.assertIsNone(reading["summary"]["candidate_code_count"])
        self.assertEqual(reading["summary"]["cv_projection"]["status"], "diagnostic_only_unresolved_input")

    def test_whitespace_unicode_and_signature_conserved(self):
        text = "\tMu ä?\nma  Tai\n"
        reading = AUDIT.parse_reading(text, signature="Tai")
        self.assertEqual("".join(p["text"] for p in reading["parts"]), text)
        self.assertEqual([p["text"] for p in reading["parts"] if p["kind"] == "signature"], ["Tai"])
        for word in reading["words"]:
            self.assertEqual("".join(t["text"] for t in word["tokens"]), word["text"])
            for token in word["tokens"]:
                a, b = token["source_span"]
                self.assertEqual(text[a:b], token["text"])

    def test_null_is_preserved_and_odd_cv_not_certified(self):
        reading = AUDIT.parse_reading("muum")
        self.assertEqual(reading["summary"]["token_counts"]["candidate_null"], 1)
        self.assertEqual(reading["summary"]["cv_projection"]["trailing_syllables"], ["mu"])
        self.assertIsNone(reading["summary"]["candidate_code_count"])


class FrozenInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = AUDIT.build_audit()

    def test_every_frozen_input_can_be_reconstructed_byte_for_byte(self):
        for path, source in self.audit["inputs"].items():
            data = source["text"].encode(source["encoding"])
            self.assertEqual(data, (AUDIT.ROOT / path).read_bytes())
            self.assertEqual(hashlib.sha256(data).hexdigest(), source["sha256"])
            self.assertEqual(len(data), source["size_bytes"])

    def test_every_character_is_accounted_for_once(self):
        for reading in self.audit["readings"].values():
            cursor = 0
            for part in reading["parts"]:
                self.assertEqual(part["source_span"], [cursor, cursor + len(part["text"])])
                cursor += len(part["text"])
            self.assertEqual(cursor, len(reading["text"]))
            for word in reading["words"]:
                cursor = 0
                for token in word["tokens"]:
                    self.assertEqual(token["word_span"], [cursor, cursor + len(token["text"])])
                    a, b = token["source_span"]
                    self.assertEqual(reading["text"][a:b], token["text"])
                    cursor += len(token["text"])
                self.assertEqual(cursor, len(word["text"]))
            self.assertTrue(reading["summary"]["all_word_characters_accounted_for"])

    def test_dudout_edits_are_all_disclosed(self):
        comp = next(c for c in self.audit["comparisons"] if c["before_reading"] == "witness:1917-06-29_0511" and c["after_reading"] == "R18_D:1917-06-29_0511")
        changes = {c["word_number"]: c for c in comp["changed_words"]}
        self.assertEqual(set(changes), {1, 3, 12})
        self.assertEqual([(e["operation"], e["before"], e["after"]) for e in changes[1]["edits"]], [("delete", "s", "")])
        self.assertEqual([(e["operation"], e["before"], e["after"]) for e in changes[3]["edits"]], [("insert", "", "j")])
        self.assertEqual([(e["operation"], e["before"], e["after"]) for e in changes[12]["edits"]], [("replace", "w", "u")])

    def test_edit_operations_reconstruct_every_changed_word(self):
        for comparison in self.audit["comparisons"]:
            for change in comparison["changed_words"]:
                old = change["before_word"]
                result, cursor = [], 0
                for edit in change["edits"]:
                    a, b = edit["before_word_span"]
                    self.assertEqual(old[a:b], edit["before"])
                    result.extend((old[cursor:a], edit["after"]))
                    cursor = b
                result.append(old[cursor:])
                self.assertEqual("".join(result), change["after_word"])

    def test_round18_counts_and_raw_witness_are_separate(self):
        for label in ("R18_B", "R18_D"):
            reading = self.audit["readings"][f"{label}:1917-06-29_0511"]
            self.assertEqual(reading["summary"]["candidate_code_count"], 67)
            self.assertEqual(reading["sheets"]["a"]["candidate_code_count"], 40)
            self.assertEqual(reading["sheets"]["b"]["candidate_code_count"], 27)
        witness = self.audit["readings"]["witness:1917-06-29_0511"]
        self.assertIsNone(witness["summary"]["candidate_code_count"])
        self.assertIn("not an independent confirmation", " ".join(self.audit["limitations"]))

    def test_stable_json_and_arbitrary_cwd_cli(self):
        self.assertEqual(AUDIT.encode_audit(self.audit), AUDIT.encode_audit(AUDIT.build_audit()))
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "audit.json"
            command = [sys.executable, str(SCRIPT), "--output", str(output)]
            subprocess.run(command, cwd=temp, check=True, capture_output=True)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), self.audit)
            subprocess.run(command + ["--check"], cwd=temp, check=True, capture_output=True)
            output.write_text("{}\n", encoding="utf-8")
            result = subprocess.run(command + ["--check"], cwd=temp, capture_output=True)
            self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
