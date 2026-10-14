"""June 1917 transcription variants (0509, 0511a, 0511b). Word-level, Dudout swap (letters 5/6 after 'o') applied optionally."""
T0509 = {
 'B': "lidajysamy vemucekyri mevecafemu pokelutazi riyecafafi cymefymeca madamymiri pujihokehe",
 'D': "lidajysamy vemucekyri mevecafemu pokelubazi riyecafafi cymefymeca madamymiri pujihohehe",
}
T0511A = {
 'B': "mupoacyobe myzoasdoke catejidoke yokigeleyi liriopen duricidule kohokycuce kuxomifumu hutadynygo capakazuye mycykafevu damoumhosy cydicapayo benyzoac hinucuge rifyjabo mahykagica fegajiriby",
 'D': "mupoacyobe myzoasdohe catyjidohe yokigeleyi liriopen duricidule kohokycuce kuxomifumu hutadynyfo capakazuye mycykafevu damoumhosy cydicapayo bemyzoac hinucuge rifygabo mahykagica fegajiriby",
}
T0511B = {
 'B': "jomoaxfojy micycoteco fuhodijige cafemigymu pokycekige rudubyrijo jorinimafy fojylisiby mikypomice miyaminoma fykazokipa",
 'D': "fomoaxfojy micycoteco fuhodigige cafenigymu pokycekige rudubyrijo gorinimafy fogylisicy mikypowice niyaminoma fykagokipa",
}
V = set('aeiouy')
def unswap(w):
    # Dudout: VC syllable at letters 5-6 after 'o' -> swap; also for 8-letter words the seam is letters 5-6 too (liri|op|en -> po ne?)
    if len(w) == 10 and w[4] in 'aeiou' and w[5] not in V and w[3] == 'o':
        return w[:4] + w[5] + w[4] + w[6:]
    return w
def fix8(w):
    # liriopen -> liripone ; benyzoac -> benyzoca  (Dudout: second half also reversed)
    if w == 'liriopen': return 'liripone'
    if w.endswith('zoac'): return w[:-2] + 'ca'
    return w
def syll(text, swap=True):
    out = []
    for w in text.split():
        if swap: w = fix8(unswap(w))
        out += [w[i:i+2] for i in range(0, len(w) - 1, 2)]
        if len(w) % 2: out.append('?' + w[-1])
    return out

# ---- Round-18 parse: vowel-initial pairs (VC) are nulls and removed ----
def syll_null(text):
    out = []
    for w in text.split():
        i = 0
        while i < len(w):
            if i + 1 < len(w) and w[i] not in 'aeiou' and w[i + 1] in 'aeiouy':
                out.append(w[i:i+2]); i += 2
            elif i + 1 < len(w) and w[i] in 'aeiou' and w[i + 1] not in 'aeiou':
                i += 2
            else:
                out.append('--'); i += 1
    return out
RAW = {
 'B': ("lidajysamy vemucekyri mevecafemu pokelutazi riyecafafi cymefymeca madamymiri pujihokehe",
       "mupoacyobe myzoasdoke catejidoke yokigeleyi liriopen duricidule kohokycuce kuxomifumu hutadynygo capakazuye mycykafevu damoumhosy cydicapayo benyzoac hinucuge rifyjabo mahykagica fegajiriby",
       "jomoaxfojy micycoteco fuhodijige cafemigymu pokycekige rudubyrijo jorinimafy fojylisiby mikypomice miyaminoma fykazokipa"),
 'D': ("lidajysamy vemucekyri mevecafemu pokelubazi riyecafafi cymefymeca madamymiri pujihohehe",
       "mupoacyobe myzoasdohe catyjidohe yokigeleyi liriopen duricidule kohokycuce kuxomifumu hutadynyfo capakazuye mycykafevu damoumhosy cydicapayo bemyzoac hinucuge rifygabo mahykagica fegajiriby",
       "fomoaxfojy micycoteco fuhodigige cafenigymu pokycekige rudubyrijo gorinimafy fogylisicy mikypowice niyaminoma fykagokipa"),
}
def null_msgs(k):
    t9, ta, tb = RAW[k]
    return {'m0509': syll_null(t9), 'm0511': syll_null(ta) + syll_null(tb)}
