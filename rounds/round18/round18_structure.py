#!/usr/bin/env python3
"""Round 18 — keyless structural tests on JACAR B03050090200 frames 0509 / 0511 (June 1917).

Pure standard library. No key, no language model. Reproduces:
  1. Three parses of the cipher stream: (A) Dudout swap, no shift; (B) Dudout swap + 0511b shifted one syllable
     (Round 16/17 / Bourdeau phase); (C) Round 18 "VC = null": every vowel-initial pair (ac, as, op, en, um, ax, ac)
     is a null syllable and is deleted.
  2. Consonant / vowel parity test (G statistic of letter x syllable-parity) with two nulls:
     shuffle syllables within a message; shuffle only among syllables at the same position inside their word.
  3. Random-removal control: delete the same number of syllables (6 on sheet a, 1 on sheet b) at random and
     compare parity G and repeated-code pairs with the VC-null parse.
  4. Code counts and repeated 4-letter codes.
Writes results/round18_structure.json.  Usage:  python3 round18_structure.py [permutations]
"""
import collections, json, math, os, random, sys

RAW = {  # B = Bourdeau-based reading (checked against the scan in Round 18), D = Dudout blind reading
    'B': ("lidajysamy vemucekyri mevecafemu pokelutazi riyecafafi cymefymeca madamymiri pujihokehe",
          "mupoacyobe myzoasdoke catejidoke yokigeleyi liriopen duricidule kohokycuce kuxomifumu hutadynygo "
          "capakazuye mycykafevu damoumhosy cydicapayo benyzoac hinucuge rifyjabo mahykagica fegajiriby",
          "jomoaxfojy micycoteco fuhodijige cafemigymu pokycekige rudubyrijo jorinimafy fojylisiby mikypomice "
          "miyaminoma fykazokipa"),
    'D': ("lidajysamy vemucekyri mevecafemu pokelubazi riyecafafi cymefymeca madamymiri pujihohehe",
          "mupoacyobe myzoasdohe catyjidohe yokigeleyi liriopen duricidule kohokycuce kuxomifumu hutadynyfo "
          "capakazuye mycykafevu damoumhosy cydicapayo bemyzoac hinucuge rifygabo mahykagica fegajiriby",
          "fomoaxfojy micycoteco fuhodigige cafenigymu pokycekige rudubyrijo gorinimafy fogylisicy mikypowice "
          "niyaminoma fykagokipa"),
}
VOW = 'aeiou'          # y is a consonant before a vowel, a vowel after a consonant


def parse_null(text):
    """Round 18 parse. Returns list of (syllable, position-in-word) ; vowel-initial pairs are dropped as nulls."""
    out = []
    for w in text.split():
        i, j = 0, 0
        while i < len(w):
            if i + 1 < len(w) and w[i] not in VOW and w[i + 1] in VOW + 'y':
                out.append((w[i:i + 2], j)); i += 2; j += 1
            elif i + 1 < len(w) and w[i] in VOW and w[i + 1] not in VOW:
                i += 2                                   # null syllable
            else:
                i += 1
    return out


def parse_swap(text):
    """Dudout parse: swap letters 5/6 when a vowel follows 'o' at the half-word seam; liriopen -> liripone,
    ..zoac -> ..zoca. Returns (syllable, position, was_vowel_initial_in_original)."""
    out = []
    for w in text.split():
        orig = [w[i:i + 2] for i in range(0, len(w) - 1, 2)]
        x = w
        if len(x) == 10 and x[3] == 'o' and x[4] in VOW and x[5] not in VOW + 'y':
            x = x[:4] + x[5] + x[4] + x[6:]
        if x == 'liriopen': x = 'liripone'
        if x.endswith('zoac'): x = x[:-2] + 'ca'
        for j in range(0, len(x) - 1, 2):
            out.append((x[j:j + 2], j // 2, orig[j // 2][0] in VOW))
    return out


def G(table):
    rows, cols, n = collections.Counter(), collections.Counter(), 0
    for (r, c), o in table.items(): rows[r] += o; cols[c] += o; n += o
    return sum(2 * o * math.log(o / (rows[r] * cols[c] / n)) for (r, c), o in table.items() if o)


def gstats(msgs):
    """msgs: list of lists of (index, syllable)."""
    tc, tv = collections.Counter(), collections.Counter()
    for m in msgs:
        for i, u in m: tc[(u[0], i % 2)] += 1; tv[(u[1], i % 2)] += 1
    return G(tc), G(tv)


def reppairs(msgs):
    c = collections.Counter()
    for m in msgs:
        d = dict(m)
        for i, u in m:
            if i % 2 == 0 and i + 1 in d: c[u + d[i + 1]] += 1
    return sum(v * (v - 1) // 2 for v in c.values()), {k: v for k, v in c.items() if v > 1}


def zscore(obs, xs):
    mu = sum(xs) / len(xs); sd = (sum((x - mu) ** 2 for x in xs) / len(xs)) ** .5
    return (obs - mu) / sd


def perm_test(msgs_with_pos, nperm, seed, within_word):
    """msgs_with_pos: list of lists of (index, syllable, pos_in_word)."""
    obs = gstats([[(i, u) for i, u, _ in m] for m in msgs_with_pos])
    rng = random.Random(seed); nc, nv = [], []
    for _ in range(nperm):
        pm = []
        for m in msgs_with_pos:
            if within_word:
                by = collections.defaultdict(list)
                for i, u, p in m: by[p].append(u)
                for v in by.values(): rng.shuffle(v)
                ptr = collections.Counter(); mm = []
                for i, u, p in m: mm.append((i, by[p][ptr[p]])); ptr[p] += 1
            else:
                us = [u for _, u, _ in m]; rng.shuffle(us); mm = [(i, u) for (i, _, _), u in zip(m, us)]
            pm.append(mm)
        g = gstats(pm); nc.append(g[0]); nv.append(g[1])
    return {'G_cons': round(obs[0], 2), 'G_vow': round(obs[1], 2), 'z_cons': round(zscore(obs[0], nc), 2),
            'z_vow': round(zscore(obs[1], nv), 2), 'p_cons': (1 + sum(x >= obs[0] for x in nc)) / (nperm + 1)}


def index(seq, start=0):
    return [(start + k, u, p) for k, (u, p) in enumerate(seq)]


def main():
    nperm = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    res = {}
    for k, (t9, ta, tb) in RAW.items():
        r = {}
        n9 = parse_null(t9); na = parse_null(ta); nb = parse_null(tb)
        sw9 = [(u, p) for u, p, _ in parse_swap(t9)]
        swa = parse_swap(ta); swb = parse_swap(tb)
        parses = {
            'A_swap_noshift': [index(sw9), index([(u, p) for u, p, _ in swa] + [(u, p) for u, p, _ in swb])],
            'B_swap_shift_b': [index(sw9), index([(u, p) for u, p, _ in swa]) +
                               index([(u, p) for u, p, _ in swb], start=len(swa) + 1)],
            'C_VC_null': [index(n9), index(na + nb)],
        }
        for name, msgs in parses.items():
            plain = [[(i, u) for i, u, _ in m] for m in msgs]
            rp, reps = reppairs(plain)
            r[name] = {
                'syllables': [len(m) for m in msgs],
                'shuffle_in_message': perm_test(msgs, nperm, 9, False),
                'shuffle_same_word_position': perm_test(msgs, nperm, 5, True),
                'repeat_pairs': rp, 'repeated_codes': reps,
            }
        # random-removal control relative to the swap parse of 0511
        sa = [u for u, _, _ in swa]; sb = [u for u, _, _ in swb]
        ka = sum(f for _, _, f in swa); kb = sum(f for _, _, f in swb)
        s9 = [(i, u) for i, (u, _) in enumerate(n9)]
        obsG = gstats([s9, [(i, u) for i, (u, _) in enumerate(na + nb)]])[0]
        obsR = reppairs([s9, [(i, u) for i, (u, _) in enumerate(na + nb)]])[0]
        rng = random.Random(11); N = 4 * nperm; geG = geR = 0
        for _ in range(N):
            ra = set(rng.sample(range(len(sa)), ka)); rb = set(rng.sample(range(len(sb)), kb))
            m = [u for i, u in enumerate(sa) if i not in ra] + [u for i, u in enumerate(sb) if i not in rb]
            mm = list(enumerate(m))
            geG += gstats([s9, mm])[0] >= obsG; geR += reppairs([s9, mm])[0] >= obsR
        r['random_removal_control'] = {'removed_sheet_a': ka, 'removed_sheet_b': kb, 'trials': N,
                                       'P_G_ge_obs': (geG + 1) / (N + 1), 'P_repeats_ge_obs': (geR + 1) / (N + 1)}
        codes9 = [n9[i][0] + n9[i + 1][0] for i in range(0, len(n9) - 1, 2)]
        s11 = na + nb
        codes11 = [s11[i][0] + s11[i + 1][0] for i in range(0, len(s11) - 1, 2)]
        r['VC_null_codes'] = {'0509': codes9, '0511': codes11, 'sheet_a_codes': len(na) / 2, 'sheet_b_codes': len(nb) / 2}
        res[k] = r
        print('==', k)
        for name in parses:
            a = r[name]
            print('  %-15s syl=%s  z_cons=%5.2f (word-pos null %5.2f)  z_vow=%5.2f  repeat_pairs=%d %s' % (
                name, a['syllables'], a['shuffle_in_message']['z_cons'], a['shuffle_same_word_position']['z_cons'],
                a['shuffle_in_message']['z_vow'], a['repeat_pairs'], a['repeated_codes']))
        print('  random removal: P(G>=obs)=%.4f  P(repeats>=obs)=%.4f' % (
            r['random_removal_control']['P_G_ge_obs'], r['random_removal_control']['P_repeats_ge_obs']))
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results'), exist_ok=True)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', 'round18_structure.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
