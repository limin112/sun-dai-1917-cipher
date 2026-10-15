#!/usr/bin/env python3
"""Lossless Round 19 audit of the frozen June readings and Round 18 emendations.

Standard library only. All offsets are Unicode code-point offsets, zero-based,
half-open; human word numbers are one-based within the telegram. The scanner
follows Round 18's greedy CV/VC recognition, but records every rejected character.
Candidate nulls remain hypotheses. Parenthesized source annotations are retained
as annotations, never silently promoted to cipher letters or resolved readings.
"""
from __future__ import annotations

import argparse
import ast
import collections
import difflib
import hashlib
import json
from pathlib import Path
import re
import string


ROOT = Path(__file__).resolve().parents[2]
VOWELS = "aeiou"
CONSONANTS = set(string.ascii_lowercase) - set(VOWELS)
TELEGRAMS = ("1917-06-24_0509", "1917-06-29_0511")
INPUTS = (
    "data/ciphertexts.json",
    "data/independent_witness.json",
    "data/morse_and_page_observations.json",
    "rounds/round18/round18_structure.py",
    "rounds/round18/WENMI_ROUND18.md",
)


def parse_word(word: str, *, word_number: int = 1, source_start: int = 0) -> list[dict]:
    """Partition every character; lowercasing is used only for classification.

    y is consonantal before a/e/i/o/u/y, and vocalic after a consonant.
    An invalid pair consumes ONE character, as in R18, to expose resynchronizing
    behavior. A final unmatched character is always recorded as trailing_char.
    """
    result = []
    i = cv_position = 0
    while i < len(word):
        j = i + 1
        a = word[i].lower()
        b = word[i + 1].lower() if i + 1 < len(word) else ""
        if word[i] == "(" and ")" in word[i:]:
            j = word.index(")", i) + 1
            kind = "annotation"
        elif a in CONSONANTS and b in VOWELS + "y" and b:
            kind, j = "cv", i + 2
        elif a in VOWELS and b in CONSONANTS:
            kind, j = "candidate_null", i + 2
        elif not b:
            kind = "trailing_char"
        else:
            kind = "invalid_char"
        token = {
            "kind": kind,
            "text": word[i:j],
            "normalized_text": word[i:j].lower(),
            "word_number": word_number,
            "word_span": [i, j],
            "source_span": [source_start + i, source_start + j],
        }
        if kind == "cv":
            token["cv_position_in_word"] = cv_position
            cv_position += 1
        result.append(token)
        i = j
    assert "".join(x["text"] for x in result) == word
    return result


def summarize(words: list[dict]) -> dict:
    tokens = [token for word in words for token in word["tokens"]]
    kinds = ("cv", "candidate_null", "invalid_char", "trailing_char", "annotation")
    counts = {kind: sum(t["kind"] == kind for t in tokens) for kind in kinds}
    characters = {kind: sum(len(t["text"]) for t in tokens if t["kind"] == kind) for kind in kinds}
    cvs = [t["normalized_text"] for t in tokens if t["kind"] == "cv"]
    unresolved = any(counts[k] for k in ("invalid_char", "trailing_char", "annotation"))
    codes = ["".join(cvs[i:i + 2]) for i in range(0, len(cvs) - 1, 2)]
    freq = collections.Counter(codes)
    return {
        "words": len(words),
        "word_characters": sum(len(w["text"]) for w in words),
        "token_counts": counts,
        "character_counts": characters,
        "all_word_characters_accounted_for": sum(characters.values()) == sum(len(w["text"]) for w in words),
        "candidate_null_locations": [t for t in tokens if t["kind"] == "candidate_null"],
        "unresolved_locations": [t for t in tokens if t["kind"] in ("invalid_char", "trailing_char", "annotation")],
        "cv_projection": {
            "status": "diagnostic_only_unresolved_input" if unresolved else "conditional_on_null_hypothesis",
            "rule": "Concatenate recognized CV tokens; omit candidate nulls and unresolved tokens. This projection is not a certified transcription.",
            "syllables": len(cvs),
            "complete_codes": codes,
            "trailing_syllables": cvs[len(codes) * 2:],
            "repeat_pairs": sum(n * (n - 1) // 2 for n in freq.values()),
            "repeated_codes": {c: n for c, n in sorted(freq.items()) if n > 1},
        },
        "candidate_code_count": len(cvs) // 2 if not unresolved and len(cvs) % 2 == 0 else None,
    }


def parse_reading(text: str, *, signature: str | None = None, boundary: int | None = None) -> dict:
    """Retain whitespace, signature, annotations and per-word source offsets."""
    spans = list(re.finditer(r"\s+|\S+", text))
    last_word = next((m for m in reversed(spans) if not m.group().isspace()), None)
    parts, words = [], []
    for m in spans:
        value = m.group()
        if value.isspace():
            kind = "whitespace"
        elif signature is not None and m is last_word and value == signature:
            kind = "signature"
        else:
            kind = "cipher_word"
        part = {"kind": kind, "text": value, "source_span": [m.start(), m.end()]}
        if kind == "cipher_word":
            number = len(words) + 1
            part["word_number"] = number
            words.append({
                "word_number": number,
                "sheet": "a" if boundary is not None and number <= boundary else "b" if boundary is not None else None,
                "text": value,
                "source_span": [m.start(), m.end()],
                "tokens": parse_word(value, word_number=number, source_start=m.start()),
            })
        parts.append(part)
    assert "".join(p["text"] for p in parts) == text
    result = {"text": text, "parts": parts, "words": words, "summary": summarize(words)}
    if boundary is not None:
        result["sheets"] = {sheet: summarize([w for w in words if w["sheet"] == sheet]) for sheet in ("a", "b")}
    return result


def word_edits(before: dict, after: dict) -> list[dict]:
    """Deterministic textual alignment, not a claim about manuscript edit history."""
    edits = []
    matcher = difflib.SequenceMatcher(a=before["text"], b=after["text"], autojunk=False)
    for operation, i, j, k, l in matcher.get_opcodes():
        if operation == "equal":
            continue
        edits.append({
            "operation": operation,
            "before": before["text"][i:j],
            "after": after["text"][k:l],
            "before_word_span": [i, j],
            "after_word_span": [k, l],
            "before_source_span": [before["source_span"][0] + i, before["source_span"][0] + j],
            "after_source_span": [after["source_span"][0] + k, after["source_span"][0] + l],
        })
    return edits


def compare_readings(before_id: str, before: dict, after_id: str, after: dict) -> dict:
    if len(before["words"]) != len(after["words"]):
        raise ValueError("Word-count mismatch: positional alignment requires explicit review")
    changes = []
    for old, new in zip(before["words"], after["words"]):
        if old["text"] != new["text"]:
            changes.append({
                "word_number": old["word_number"], "sheet": old["sheet"],
                "before_word": old["text"], "after_word": new["text"],
                "edits": word_edits(old, new),
            })
    return {
        "before_reading": before_id, "after_reading": after_id,
        "alignment": "Words by telegram word number; difflib.SequenceMatcher characters, autojunk=False. Repeated-letter alignments are not unique historical evidence.",
        "changed_words": changes,
        "structure_delta": {
            "cv_syllables": after["summary"]["token_counts"]["cv"] - before["summary"]["token_counts"]["cv"],
            "candidate_nulls": after["summary"]["token_counts"]["candidate_null"] - before["summary"]["token_counts"]["candidate_null"],
            "before_candidate_code_count": before["summary"]["candidate_code_count"],
            "after_candidate_code_count": after["summary"]["candidate_code_count"],
        },
    }


def load_round18_raw(source: str) -> dict:
    """Read the archived literals without importing/executing historical code."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "RAW" for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("Round 18 RAW assignment not found")


def review_queue(readings: dict, comparisons: list[dict]) -> list[dict]:
    reasons = collections.defaultdict(set)
    for comp in comparisons:
        if comp["before_reading"].startswith("witness:") and comp["after_reading"].startswith("R18_D:"):
            telegram = comp["before_reading"].split(":", 1)[1]
            for change in comp["changed_words"]:
                reasons[(telegram, change["word_number"])].add("R18 D differs from frozen blind witness")
    for reading_id, reading in readings.items():
        telegram = reading_id.split(":", 1)[1]
        for word in reading["words"]:
            if any(t["kind"] in ("invalid_char", "trailing_char", "annotation") for t in word["tokens"]):
                reasons[(telegram, word["word_number"])].add("Unresolved character or source annotation")
            if any(t["kind"] == "candidate_null" for t in word["tokens"]):
                reasons[(telegram, word["word_number"])].add("Vowel-initial pair requires manuscript review; null status unproven")
    reasons[(TELEGRAMS[1], 7)].add("R18 report flags strongest negative within-word phase; raw ee versus R18 ce")
    result = []
    for (telegram, number), why in reasons.items():
        priority = 1 if any("R18 D differs" in x for x in why) else 2 if any("Unresolved" in x or "phase" in x for x in why) else 3
        result.append({
            "priority": priority, "telegram": telegram, "word_number": number,
            "reasons": sorted(why),
            "readings": {name.split(":")[0]: value["words"][number - 1]["text"] for name, value in readings.items() if name.endswith(":" + telegram)},
            "verification": "Not newly checked against an image in Round 19; review queue only.",
        })
    return sorted(result, key=lambda x: (x["priority"], x["telegram"], x["word_number"]))


def build_audit(root: Path = ROOT) -> dict:
    sources = {}
    for name in INPUTS:
        data = (root / name).read_bytes()
        sources[name] = {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data), "encoding": "utf-8", "text": data.decode("utf-8")}
    raw = json.loads(sources[INPUTS[0]]["text"])
    witness = json.loads(sources[INPUTS[1]]["text"])
    observations = json.loads(sources[INPUTS[2]]["text"])
    r18 = load_round18_raw(sources[INPUTS[3]]["text"])
    boundary = observations["0511"]["sheet_boundary_after_cipher_word"]
    readings = {}
    for telegram in TELEGRAMS:
        entry = witness["telegrams"][telegram]
        sheet_boundary = boundary if telegram == TELEGRAMS[1] else None
        corpus = {
            "raw_notes": (raw["raw_june_notes"][telegram], entry["cleartext_signature"]),
            "program_variant": (raw["analysis_variants"][telegram], None),
            "witness": (" ".join(entry["words"]), None),
            "R18_B": (r18["B"][0] if telegram == TELEGRAMS[0] else " ".join(r18["B"][1:]), None),
            "R18_D": (r18["D"][0] if telegram == TELEGRAMS[0] else " ".join(r18["D"][1:]), None),
        }
        for label, (text, signature) in corpus.items():
            reading = parse_reading(text, signature=signature, boundary=sheet_boundary)
            reading["provenance"] = {
                "raw_notes": "Literal frozen Bourdeau notes, including unresolved parenthesized annotations and signature.",
                "program_variant": "Frozen historical program input; not an image-certified reading.",
                "witness": "Frozen independent human reading; uncertain, not uniquely certified.",
                "R18_B": "Archived Round 18 Bourdeau-based emended reading; image checks are historical report claims, not newly verified here.",
                "R18_D": "Archived Round 18 emended Dudout-based reading; must not be labelled the untouched blind witness.",
            }[label]
            readings[f"{label}:{telegram}"] = reading
    comparisons = []
    for telegram in TELEGRAMS:
        for base in ("raw_notes", "program_variant", "witness"):
            for target in ("R18_B", "R18_D"):
                a, b = f"{base}:{telegram}", f"{target}:{telegram}"
                comparisons.append(compare_readings(a, readings[a], b, readings[b]))
    return {
        "schema_version": 1,
        "status": "unsolved; no plaintext or key is asserted",
        "offset_convention": "Zero-based half-open Unicode code-point spans; word_number is one-based within the telegram. Insertions use an empty before span.",
        "scope": "Local frozen-input provenance and character accounting only; candidate nulls are hypotheses, not a newly proved cipher rule.",
        "limitations": [
            "Character recognition follows the Round 18 greedy scanner, including resynchronization after one invalid character; it is not a global optimum or uniquely correct syllabification.",
            "Parenthesized source notes remain unresolved annotation tokens; no branch choice is inferred from them.",
            "CV projections drop unresolved tokens only for diagnosis and are explicitly flagged; candidate_code_count is null when unresolved tokens or an odd CV count remain.",
            "R18_D includes edits to the frozen independent witness and is not an independent confirmation of those edits.",
            "The 0511 sheet boundary follows the frozen page observation after word 18; no new image reading was performed.",
        ],
        "inputs": sources,
        "readings": readings,
        "comparisons": comparisons,
        "image_review_queue": review_queue(readings, comparisons),
    }


def encode_audit(audit: dict) -> str:
    return json.dumps(audit, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT, help="Repository root containing frozen data/ and rounds/round18/")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "results/provenance_audit.json", help="JSON output path (default is next to this script, independent of cwd)")
    parser.add_argument("--check", action="store_true", help="Verify output exactly matches regenerated stable JSON without writing")
    args = parser.parse_args(argv)
    encoded = encode_audit(build_audit(args.repo_root))
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != encoded:
            parser.exit(1, f"Audit differs or is missing: {args.output}\n")
        print(f"Verified: {args.output}")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
        print(f"Wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
