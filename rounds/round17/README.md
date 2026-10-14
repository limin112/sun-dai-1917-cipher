# Round 17 reproducibility and rights

Run `python3 round17_analysis.py` using Python 3.8+ standard library. It checks the byte SHA-256 of the original Round16 frozen `ciphertexts.json`; it does not modify either prior raw or analytic variant. Source transcriptions and their copyrights are credited in `sources/source_register.json`. No archival image files are included; JACAR photos are linked by URL and Git blob SHA.

Outputs: deterministic Monte Carlo conditional within-word shuffles (N=50,000; N=12,000 whole-sheet), 8-phase look-elsewhere shuffle (N=12,000), 1917 March independent known-key cross-telegram positive control (N=12,000), exact Morse Ä enumeration, page-boundary length QA, and explicit alternate-read sensitivities. All results are structural and none is decrypted June Chinese.

Phase statistics are exploratory: the hypothesized four-letter coding and segment phase were previously inspected; conditional permutation p-values do not cover the entire 16-round research history or guarantee a decipherment.
