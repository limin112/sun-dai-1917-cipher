#!/usr/bin/env python3
"""Conditional sensitivity checks for Round 18; standard library, no LM or keys.

Read the archived RAW literal without executing the archived script. Never rewrite
archives/data. Every output is exploratory and conditional on those edited readings.
"""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[2]
VOWELS = "aeiou"
PARSES = ("A_swap_noshift", "B_swap_shift_b", "C_VC_null")


def read_inputs():
    path = ROOT / "rounds/round18/round18_structure.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    raw = next(ast.literal_eval(node.value) for node in tree.body
               if isinstance(node, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "RAW" for t in node.targets))
    return raw


def fixed_pairs(text):
    """No resynchronization, deletion, or repair; reject odd-length words.

    Each record is (token, word index, original pair slot within the word).
    """
    out = []
    for word_id, word in enumerate(text.split()):
        if len(word) % 2:
            raise ValueError(f"odd-length word {word_id}: {word}")
        out.extend((word[i:i + 2], word_id, i // 2) for i in range(0, len(word), 2))
    return out


def is_vc(token):
    return token[0] in VOWELS and token[1] not in VOWELS


def normalize(token):
    return token[::-1] if is_vc(token) else token


def retained_positions(records, compressed=False):
    counts = Counter()
    out = []
    for token, word, slot in records:
        if is_vc(token):
            continue
        out.append((token, counts[word] if compressed else slot))
        counts[word] += 1
    return out


def g_stat(table):
    rows, cols = Counter(), Counter()
    for (row, col), count in table.items():
        rows[row] += count
        cols[col] += count
    n = sum(table.values())
    return sum(2 * count * math.log(count * n / (rows[row] * cols[col]))
               for (row, col), count in table.items() if count)


def statistics(messages):
    """First-letter parity G and repeated four-letter-code pair count.

    First letters include vowels when raw random deletion leaves VC tokens.
    Missing indices must not be bridged when collecting complete codes.
    """
    table, codes = Counter(), Counter()
    for message in messages:
        values = dict(message)
        for index, token in message:
            table[token[0], index % 2] += 1
            if index % 2 == 0 and index + 1 in values:
                codes[token + values[index + 1]] += 1
    return g_stat(table), sum(n * (n - 1) // 2 for n in codes.values())


def candidate(pages, masks, name):
    if name not in PARSES:
        raise ValueError(name)
    selected = [[t for i, t in enumerate(page)
                 if name != "C_VC_null" or i not in masks[j]]
                for j, page in enumerate(pages)]
    start_b = len(selected[1]) + (name == "B_swap_shift_b")
    return [list(enumerate(selected[0])),
            list(enumerate(selected[1])) + list(enumerate(selected[2], start_b))]


def tail(observed, samples):
    exceedances = sum(value >= observed for value in samples)
    n = len(samples)
    p = (exceedances + 1) / (n + 1)
    # Wilson interval for the Monte Carlo Bernoulli exceedance probability;
    # this is simulation uncertainty, not uncertainty of the historical claim.
    z, rate = 1.959963984540054, exceedances / n
    denominator = 1 + z * z / n
    center = (rate + z * z / (2 * n)) / denominator
    half = z * math.sqrt(rate * (1 - rate) / n + z * z / (4 * n * n)) / denominator
    return {"observed": observed, "exceedances": exceedances, "trials": n,
            "p_plus1": p, "mc_wilson95": [max(0., center - half), min(1., center + half)]}


def deletion_control(pages, masks, trials, seed, normalized):
    payloads = [[normalize(t) if normalized else t for t, _, _ in page] for page in pages]
    observed = statistics(candidate(payloads, masks, "C_VC_null"))
    rng = random.Random(seed)
    samples = [[], []]
    for _ in range(trials):
        removals = [set(rng.sample(range(len(page)), len(mask)))
                    for page, mask in zip(payloads, masks)]
        values = statistics(candidate(payloads, removals, "C_VC_null"))
        for results, value in zip(samples, values):
            results.append(value)
    return {"seed": seed, "removed_by_page": [len(m) for m in masks],
            "first_letter_G": tail(observed[0], samples[0]),
            "repeat_pairs": tail(observed[1], samples[1])}


def position_control(pages, trials, seed, compressed):
    # Match R18 message-level strata, allowing shuffle between the two 0511 pages.
    groups = [retained_positions(pages[0], compressed),
              retained_positions(pages[1], compressed) + retained_positions(pages[2], compressed)]
    observed = statistics([list(enumerate(t for t, _ in group)) for group in groups])[0]
    rng, samples = random.Random(seed), []
    for _ in range(trials):
        messages = []
        for group in groups:
            positions = defaultdict(list)
            for index, (_, pos) in enumerate(group):
                positions[pos].append(index)
            values = [token for token, _ in group]
            for indexes in positions.values():
                shuffled = [values[i] for i in indexes]
                rng.shuffle(shuffled)
                for index, token in zip(indexes, shuffled):
                    values[index] = token
            messages.append(list(enumerate(values)))
        samples.append(statistics(messages)[0])
    return {"seed": seed, "stratum": "retained_slot" if compressed else "original_fixed_pair_slot",
            "first_letter_G": tail(observed, samples)}


def finite_family_control(readings, trials, seed):
    """Shared pagewise index permutations over 2 readings x 3 fixed parses.

    Keep deletion masks and index-gap choices fixed, shuffle normalized payloads
    across slots. Apply each same index permutation to B and D; thus transcription
    disagreements remain paired. This tests only the explicitly named six choices.
    """
    payloads = {key: [[normalize(t) for t, _, _ in page] for page in pages]
                for key, (pages, _) in readings.items()}
    shapes = {tuple(map(len, pages)) for pages in payloads.values()}
    if len(shapes) != 1:
        raise ValueError("Paired permutations require aligned reading lengths")
    names = [(key, name) for key in readings for name in PARSES]
    observed = {f"{key}/{name}": statistics(candidate(payloads[key], readings[key][1], name))
                for key, name in names}
    draws = {name: [[], []] for name in observed}
    maxima = [[], []]
    rng = random.Random(seed)
    for _ in range(trials):
        permutations = [list(range(length)) for length in next(iter(shapes))]
        for order in permutations:
            rng.shuffle(order)
        values = []
        for key, name in names:
            shuffled = [[page[i] for i in order] for page, order in zip(payloads[key], permutations)]
            value = statistics(candidate(shuffled, readings[key][1], name))
            values.append(value)
            for sample, item in zip(draws[f"{key}/{name}"], value):
                sample.append(item)
        for dimension in range(2):
            maxima[dimension].append(max(value[dimension] for value in values))
    metrics = ("first_letter_G", "repeat_pairs")
    return {"seed": seed, "candidate_count": len(names), "candidate_names": list(observed),
            "null": "paired normalized-token permutation within each page; masks and parses fixed",
            "family_max": {metric: tail(max(value[j] for value in observed.values()), maxima[j])
                           for j, metric in enumerate(metrics)},
            "candidates": {name: {metric: {"unadjusted": tail(value[j], draws[name][j]),
                                          "max_adjusted": tail(value[j], maxima[j])}
                                  for j, metric in enumerate(metrics)}
                           for name, value in observed.items()},
            "scope": "Six frozen candidates only; endpoints separate; not full R1-R18 selection correction"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(trials=4000, seed=19019):
    if trials < 1:
        raise ValueError("trials must be positive")
    raw = read_inputs()
    readings = {}
    results = {}
    for key, texts in raw.items():
        pages = [fixed_pairs(text) for text in texts]
        masks = [{i for i, (t, _, _) in enumerate(page) if is_vc(t)} for page in pages]
        readings[key] = pages, masks
        changed_slots = sum(original != retained for page in pages
                            for (_, original), (_, retained) in zip(retained_positions(page), retained_positions(page, True)))
        symbols = {t for page in pages for t, _, _ in page if not is_vc(t)}
        entropy = sum(math.log2(i) for i in range(101 - len(symbols), 101))
        results[key] = {
            "page_pair_counts": list(map(len, pages)),
            "vc_masks_zero_based": [sorted(mask) for mask in masks],
            "retained_tokens_with_changed_word_slot": changed_slots,
            "retained_distinct_symbols": len(symbols),
            "uniform_injective_key_entropy_bits": entropy,
            "hypothetical_H_over_D_at_5_bits_per_code": entropy / 5,
            "random_deletion_raw_pairs": deletion_control(pages, masks, 4 * trials, seed, False),
            "random_deletion_normalized_pairs": deletion_control(pages, masks, 4 * trials, seed, True),
            "word_position_original": position_control(pages, trials, seed + 1, False),
            "word_position_compressed": position_control(pages, trials, seed + 1, True),
        }
    inputs = ["rounds/round18/round18_structure.py", "rounds/round18/results/round18_structure.json",
              "rounds/round18/results/controls/controls_and_searches.md", "data/ciphertexts.json",
              "data/independent_witness.json"]
    return {"schema_version": 1, "status": "exploratory sensitivity; no new plaintext",
            "parameters": {"trials": trials, "deletion_trials": 4 * trials, "seed": seed},
            "input_sha256": {p: sha(ROOT / p) for p in inputs},
            "raw_literal_sha256": hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest(),
            "readings": results,
            "finite_family_selection": finite_family_control(readings, trials, seed + 2),
            "limitations": ["RAW B/D are edited R18 hypotheses, not literal independent witness readings",
                            "Exchangeability models are sensitivity assumptions, not a historical generative model",
                            "Raw-pair deletion G includes vowel first letters; normalization changes reference distribution",
                            "No correction for unrecorded prior searches, transcription choices, or metric selection",
                            "Uniform injection and 5 bits/code are hypothetical, not measured entropy/redundancy"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=19019)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("results") / "selection_controls.json")
    args = parser.parse_args()
    result = run(args.trials, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
