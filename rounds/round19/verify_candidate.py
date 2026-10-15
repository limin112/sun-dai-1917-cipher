#!/usr/bin/env python3
"""Check a supplied injective CV-syllable -> 00..99 table mechanically.

Passing is conditional consistency, never historical authentication or a claim
that the numeric stream is Chinese plaintext. No candidate table is generated.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("candidate_provenance_audit", HERE / "provenance_audit.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
READINGS = tuple(f"{label}:{telegram}" for label in ("raw_notes", "program_variant", "witness", "R18_B", "R18_D") for telegram in AUDIT.TELEGRAMS)
VALIDATION_LEVEL = "conditional_mechanical_consistency_only"


class VerificationError(ValueError):
    def __init__(self, code: str, message: str, details=None):
        super().__init__(message)
        self.code = code
        self.details = details


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError("duplicate_mapping_key", f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def validate_mapping(mapping: dict) -> dict:
    """Validate ALL supplied entries, including codes absent from this reading."""
    if not isinstance(mapping, dict) or not mapping:
        raise VerificationError("invalid_mapping", "Mapping must be a nonempty JSON object of CV syllable -> two-digit string.")
    inverse = {}
    for code, number in mapping.items():
        if not isinstance(code, str) or not re.fullmatch(r"[a-z]{2}", code):
            raise VerificationError("invalid_code", f"Key must be two lowercase ASCII letters: {code!r}")
        tokens = AUDIT.parse_word(code)
        if len(tokens) != 1 or tokens[0]["kind"] != "cv":
            raise VerificationError("invalid_code", f"Key is not exactly one CV syllable: {code!r}")
        if not isinstance(number, str) or not re.fullmatch(r"[0-9]{2}", number):
            raise VerificationError("invalid_value", f"Value for {code!r} must be a string in 00..99: {number!r}")
        if number in inverse:
            raise VerificationError("noninjective_mapping", f"Value {number!r} is assigned to both {inverse[number]!r} and {code!r}.")
        inverse[number] = code
    return inverse


def load_mapping(data: bytes) -> dict:
    mapping = json.loads(data.decode("utf-8"), object_pairs_hook=unique_object)
    validate_mapping(mapping)
    return mapping


def select_reading(reading_id: str, *, accept_round18_emendations=False) -> tuple[dict, dict]:
    if reading_id not in READINGS:
        raise VerificationError("unknown_reading", f"Unknown repository reading: {reading_id}")
    if reading_id.startswith(("R18_B:", "R18_D:")) and not accept_round18_emendations:
        raise VerificationError("emendation_acceptance_required", "R18 readings require --accept-round18-emendations; their edits are assumptions, not independent validation.")
    audit = AUDIT.build_audit()
    reading = audit["readings"][reading_id]
    sources = {name: {"sha256": source["sha256"], "size_bytes": source["size_bytes"]} for name, source in audit["inputs"].items()}
    return reading, sources


def verify_candidate(text: str, mapping: dict, *, reading_id="custom_text", signature=None,
                     accept_vc_nulls=False, accept_round18_emendations=False) -> dict:
    inverse = validate_mapping(mapping)
    if reading_id.startswith(("R18_B:", "R18_D:")) and not accept_round18_emendations:
        raise VerificationError("emendation_acceptance_required", "R18 readings require explicit acceptance of their emendations.")
    # The scanner lowercases for recognition; restrict letters first so Unicode
    # case conversion cannot silently promote e.g. the Kelvin sign to ASCII k.
    non_ascii = [{"text": c, "source_span": [i, i + 1]} for i, c in enumerate(text) if not c.isascii() and not c.isspace()]
    if non_ascii:
        raise VerificationError("non_ascii_cipher_character", "Cipher letters must be ASCII; Unicode substitutions are not normalized.", non_ascii)
    reading = AUDIT.parse_reading(text, signature=signature)
    tokens = [token for word in reading["words"] for token in word["tokens"]]
    unresolved = [t for t in tokens if t["kind"] not in ("cv", "candidate_null")]
    if unresolved:
        raise VerificationError("unresolved_input", "Reading contains unexplained characters, source annotations, or a trailing character; no tokens may be dropped.", unresolved)
    nulls = [t for t in tokens if t["kind"] == "candidate_null"]
    if nulls and not accept_vc_nulls:
        raise VerificationError("null_acceptance_required", "Reading contains vowel-initial pairs; --accept-vc-nulls explicitly assumes they are nulls.", nulls)
    cvs = [t for t in tokens if t["kind"] == "cv"]
    if not cvs:
        raise VerificationError("empty_ciphertext", "Reading contains no complete ciphertext code.")
    if len(cvs) % 2:
        raise VerificationError("incomplete_code", "An unmatched CV syllable remains after global pairing; it may not be truncated.", cvs[-1:])
    codes = [cvs[i]["normalized_text"] + cvs[i + 1]["normalized_text"] for i in range(0, len(cvs), 2)]
    observed_syllables = {t["normalized_text"] for t in cvs}
    missing = sorted(observed_syllables - set(mapping))
    if missing:
        raise VerificationError("missing_mapping", "Table does not cover every CV syllable in the selected reading.", missing)

    records = []
    # Rebuild each cipher token from inverse-table output, not original letters.
    # Case, null text, signature and whitespace remain supplied layout metadata.
    replacements = {}
    for index, code in enumerate(codes):
        pair = cvs[index * 2:index * 2 + 2]
        values = [mapping[t["normalized_text"]] for t in pair]
        number = "".join(values)
        reencryption = "".join(inverse[value] for value in values)
        for syllable_index, token in enumerate(pair):
            syllable = reencryption[syllable_index * 2:syllable_index * 2 + 2]
            replacements[tuple(token["source_span"])] = "".join(c.upper() if old.isupper() else c for c, old in zip(syllable, token["text"]))
        records.append({"code_index": index, "cipher_code": code, "numeric_value": number,
                        "syllable_values": values,
                        "reencrypted_code": reencryption, "syllables": pair,
                        "crosses_word_boundary": pair[0]["word_number"] != pair[1]["word_number"]})
    chunks, cursor = [], 0
    for (start, end), replacement in sorted(replacements.items()):
        chunks.extend((text[cursor:start], replacement))
        cursor = end
    chunks.append(text[cursor:])
    reconstructed = "".join(chunks)
    if reconstructed != text:
        raise VerificationError("roundtrip_mismatch", "Inverse-table reconstruction did not reproduce the selected input exactly.")
    canonical = json.dumps(mapping, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": 1,
        "status": "pass",
        "validation_level": VALIDATION_LEVEL,
        "historical_authentication": False,
        "independent_validation": False,
        "reading_id": reading_id,
        "input_sha256": sha256(text.encode("utf-8")),
        "mapping_canonical_sha256": sha256(canonical),
        "model": {
            "rule": "One injective table maps each CV syllable to a two-digit string in 00..99; two consecutive syllables yield one four-digit CTC label.",
            "pairing": "Global within selected telegram, phase zero, across word boundaries after hypothesized VC null removal.",
            "y_rule": "y is consonantal before a/e/i/o/u/y and vocalic after a consonant, following the Round 19 scanner.",
            "vc_null_hypothesis_accepted": accept_vc_nulls,
            "round18_emendations_accepted": accept_round18_emendations,
            "coverage": "Every observed CV syllable must be mapped. Unobserved syllables need not be supplied; this does not certify a complete historical 100-entry table.",
        },
        "mapping_entries": len(mapping),
        "observed_unique_codes": len(set(codes)),
        "observed_unique_syllables": len(observed_syllables),
        "unused_mapping_syllables": sorted(set(mapping) - observed_syllables),
        "numeric_values": [record["numeric_value"] for record in records],
        "numeric_stream": "".join(record["numeric_value"] for record in records),
        "codes": records,
        "candidate_null_locations": nulls,
        "layout": reading["parts"],
        "reencrypted_text": reconstructed,
        "reencrypted_sha256": sha256(reconstructed.encode("utf-8")),
        "exact_input_roundtrip": True,
        "limitations": [
            "This deterministic inverse-table check is tautological for any valid injective supplied table; it does not establish that the table or reading is historically correct.",
            "Nulls, word boundaries, whitespace, original letter case and any declared cleartext signature are supplied layout side information, not recovered from the numeric stream.",
            "Numeric values are four-digit CTC labels formed from two syllable values, not decoded Chinese characters; no telegraph-code dictionary, language score or independent evidence is checked.",
            "Custom-file provenance is caller supplied; renaming an emended reading as a custom file does not authenticate it.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapping", required=True, type=Path, help="JSON object mapping lowercase two-letter CV syllables to two-digit strings")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--reading", choices=READINGS, help="Explicit frozen or archived repository reading")
    selection.add_argument("--text-file", type=Path, help="UTF-8 custom ciphertext; provenance remains caller supplied")
    parser.add_argument("--accept-vc-nulls", action="store_true")
    parser.add_argument("--accept-round18-emendations", action="store_true")
    parser.add_argument("--output", type=Path, help="Write JSON here instead of stdout")
    args = parser.parse_args(argv)
    report = {"schema_version": 1, "status": "fail", "validation_level": VALIDATION_LEVEL,
              "historical_authentication": False, "independent_validation": False,
              "reading_id": args.reading or "custom_text"}
    try:
        mapping_bytes = args.mapping.read_bytes()
        report["mapping_file_sha256"] = sha256(mapping_bytes)
        if args.reading:
            selected, sources = select_reading(args.reading, accept_round18_emendations=args.accept_round18_emendations)
            text = selected["text"]
            signatures = [p["text"] for p in selected["parts"] if p["kind"] == "signature"]
            signature = signatures[0] if signatures else None
            report["reading_provenance"] = selected["provenance"]
            report["source_files"] = sources
        else:
            raw = args.text_file.read_bytes()
            report["input_file_sha256"] = sha256(raw)
            text = raw.decode("utf-8")
            signature = None
            report["reading_provenance"] = "Custom UTF-8 file; no independent source verification."
        report["input_sha256"] = sha256(text.encode("utf-8"))
        mapping = load_mapping(mapping_bytes)
        report.update(verify_candidate(text, mapping, reading_id=report["reading_id"], signature=signature,
                                       accept_vc_nulls=args.accept_vc_nulls,
                                       accept_round18_emendations=args.accept_round18_emendations))
    except VerificationError as exc:
        report["error"] = {"code": exc.code, "message": str(exc), "details": exc.details}
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        report["error"] = {"code": "input_error", "message": str(exc)}
    encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        # No implicit directory creation or repository writes: output is opt-in.
        try:
            args.output.write_text(encoded, encoding="utf-8")
        except OSError as exc:
            print(f"Cannot write output: {exc}", file=sys.stderr)
            return 2
    else:
        print(encoded, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
