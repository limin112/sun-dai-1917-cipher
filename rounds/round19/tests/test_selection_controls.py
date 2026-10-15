import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "selection_controls.py"
spec = importlib.util.spec_from_file_location("selection_controls", MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class SelectionControlsTests(unittest.TestCase):
    def test_fixed_slots_survive_deletion(self):
        pairs = audit.fixed_pairs("mupoacyobe")
        self.assertEqual(audit.retained_positions(pairs), [("mu", 0), ("po", 1), ("yo", 3), ("be", 4)])
        self.assertEqual(audit.retained_positions(pairs, True), [("mu", 0), ("po", 1), ("yo", 2), ("be", 3)])
        with self.assertRaises(ValueError):
            audit.fixed_pairs("muposacyobe")

    def test_gap_does_not_create_a_code(self):
        self.assertEqual(audit.statistics([[(0, "ca"), (2, "fe"), (3, "ca"), (4, "fe")]])[1], 0)
        self.assertEqual(audit.statistics([list(enumerate(["ca", "fe", "ca", "fe"]))])[1], 1)

    def test_observed_deletion_commutes_with_normalization(self):
        for texts in audit.read_inputs().values():
            pages = [audit.fixed_pairs(text) for text in texts]
            masks = [{i for i, (token, _, _) in enumerate(page) if audit.is_vc(token)} for page in pages]
            raw = [[token for token, _, _ in page] for page in pages]
            normalized = [[audit.normalize(token) for token in page] for page in raw]
            self.assertEqual(audit.candidate(raw, masks, "C_VC_null"),
                             audit.candidate(normalized, masks, "C_VC_null"))

    def test_agrees_with_archived_observed_results(self):
        import json
        archive = json.loads((audit.ROOT / "rounds/round18/results/round18_structure.json").read_text())
        for key, texts in audit.read_inputs().items():
            pages = [audit.fixed_pairs(text) for text in texts]
            masks = [{i for i, (token, _, _) in enumerate(page) if audit.is_vc(token)} for page in pages]
            payloads = [[audit.normalize(token) for token, _, _ in page] for page in pages]
            self.assertEqual(list(map(len, pages)), [40, 86, 55])
            self.assertEqual(list(map(len, masks)), [0, 6, 1])
            for name in audit.PARSES:
                g, repeats = audit.statistics(audit.candidate(payloads, masks, name))
                self.assertEqual(round(g, 2), archive[key][name]["shuffle_in_message"]["G_cons"])
                self.assertEqual(repeats, archive[key][name]["repeat_pairs"])

    def test_plus_one_and_mc_interval(self):
        result = audit.tail(3, [0, 1, 2])
        self.assertEqual(result["p_plus1"], .25)
        self.assertEqual(result["exceedances"], 0)
        self.assertGreater(result["mc_wilson95"][1], 0)

    def test_deterministic_and_adjustment_monotone(self):
        first = audit.run(12, 123)
        self.assertEqual(first, audit.run(12, 123))
        family = first["finite_family_selection"]
        self.assertEqual(family["candidate_count"], 6)
        for candidate in family["candidates"].values():
            for metric in candidate.values():
                self.assertGreaterEqual(metric["max_adjusted"]["p_plus1"], metric["unadjusted"]["p_plus1"])


if __name__ == "__main__":
    unittest.main()
