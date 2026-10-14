#!/usr/bin/env python3
"""Round 15 cautious original-source/target crosswalk, not a decryptor.

Independent fixtures verify the date-range arithmetic. Reproducible and stdlib-only.
Actual primary scans were visually read; this script does not claim image/OCR access.
"""
import json, hashlib
from datetime import date,timedelta
from pathlib import Path
BASE=Path(__file__).resolve().parent
f=BASE/'input/ciphertexts.json'
original=f.read_bytes()
sha=hashlib.sha256(original).hexdigest()
assert sha=='620e469ec26d6534df2dbad0553d79844f1d9df8e68e47a95194a1c0563a8136', (sha,'unexpected source')
record=json.loads(original)
assert record['image_verified'] is False
notes=record['raw_june_notes']; analysis=record['analysis_variants']
assert 'kohokycuee' in notes['1917-06-29_0511'].lower()
assert 'vemucayri' in notes['1917-06-24_0509'].lower()
assert 'hutadyny(y)go' in notes['1917-06-29_0511'].lower()
assert 'hutadynyyg' in analysis['1917-06-29_0511']

def departures(arrival_low,arrival_high,days_low,days_high):
    """Inclusive and elapsed day count interpretations, strictly exploratory."""
    return (arrival_low + timedelta(days=days_low-1), arrival_high + timedelta(days=days_high))

def test_controls():
    # Synthetic positive: exact date and 3 elapsed days => possible departure includes 4th.
    t=departures(date(1917,6,21),date(1917,6,21),3,3)
    assert t==(date(1917,6,23),date(1917,6,24))
    # Synthetic negative: Jun29 cannot belong to a departure window ending Jun26.
    assert date(1917,6,29)>departures(date(1917,6,20),date(1917,6,22),3,4)[1]
    # Confirm any June archive byte is not marked verified by this procedure.
    assert record['image_verified'] is False
    return {'synthetic_date_arithmetic_positive':'PASS','synthetic_date_window_negative':'PASS','target_image_guard':'PASS'}

controls=test_controls()
# '大約是二十一罷' conservatively broadened +/-1 day; duration =3-4 days.
lo,hi=departures(date(1917,6,20),date(1917,6,22),3,4)
result={
 'research_date':'2026-10-11','ciphertext_sha256':sha,
 'original_archive_image_verified':False,'verified_june_characters':0,'historical_key_found':False,
 'evidence_scope':'1928 first-person retrospective, not the 1917 letter or June original image',
 'observed_arrival':'about 1917-06-21 (first-person 1928 book p103)',
 'sensitivity_arrival_assumption':'[1917-06-20,1917-06-22] is a testing window, not historical fact',
 'possible_tokyo_departure_interval':[str(lo),str(hi)],
 'june29_telegram_transcription':'Tokyo -> Shanghai; date 1917-06-29, public 3rd-party notes only',
 'conditional_timing_tension': date(1917,6,29)>hi,
 'timing_tension_is_proof_of_archival_mistake':False,
 'possible_explanations':['retrospective date uncertainty','travel/return timing differs','Tokyo origin or sending date must be checked against actual archived telegram','multiple trips cannot be excluded'],
 'novel_actionable_search_lead':'Look for a detailed report letter authored Dai Jitao to Sun Yat-sen, c. June 21-29 1917, covering meetings with Akiyama Saneyuki and Tanaka Giichi. Search independent Chinese/Japanese archival letter registers.',
 'raw_vs_analysis_variant_kept_separate': True,
 'june_anomalies_left_untouched':{'0509':'vemucayri','0511':'kohokycuee; hutadyny(y)go'},
 'algorithm_controls':controls,
 'target_plaintext_candidates':[],
 'important_caution':'No algorithm produced any verified Chinese for 0509/0511; a historical report mentioned in a memoir may differ completely from a telegram.'
}
output=BASE/'results/timeline_audit.json';output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
