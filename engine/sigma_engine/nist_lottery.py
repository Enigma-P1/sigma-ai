"""NIST StRD reference dataset for stats-core reference tests (M2).

Source: NIST Statistical Reference Datasets (StRD), Univariate Summary
Statistics collection, "Lower Level of Difficulty" dataset "Lottery"
(New Jersey pick-3 lottery, observed/"real world" data):
https://www.itl.nist.gov/div898/strd/univ/data/Lottery.dat

Fetched live in-container on 2026-08-07: DATA below was transcribed from
that file's 218-observation data section (lines 61-278), and
CERTIFIED_MEAN / CERTIFIED_STDEV / CERTIFIED_AUTOCORRELATION were
transcribed verbatim from its "Certified Values" header (lines 41-43).
Recomputing mean/stdev over DATA reproduces the certified figures to
within 1e-9 relative tolerance (see tests/test_stats_descriptive.py) --
the transcription is self-verifying, not just copied by hand.
"""

DATASET_NAME = "Lottery"

# 218 observations, NIST StRD Lottery.dat lines 61-278.
DATA: list[float] = [
    162, 671, 933, 414, 788, 730, 817, 33, 536, 875,
    670, 236, 473, 167, 877, 980, 316, 950, 456, 92,
    517, 557, 956, 954, 104, 178, 794, 278, 147, 773,
    437, 435, 502, 610, 582, 780, 689, 562, 964, 791,
    28, 97, 848, 281, 858, 538, 660, 972, 671, 613,
    867, 448, 738, 966, 139, 636, 847, 659, 754, 243,
    122, 455, 195, 968, 793, 59, 730, 361, 574, 522,
    97, 762, 431, 158, 429, 414, 22, 629, 788, 999,
    187, 215, 810, 782, 47, 34, 108, 986, 25, 644,
    829, 630, 315, 567, 919, 331, 207, 412, 242, 607,
    668, 944, 749, 168, 864, 442, 533, 805, 372, 63,
    458, 777, 416, 340, 436, 140, 919, 350, 510, 572,
    905, 900, 85, 389, 473, 758, 444, 169, 625, 692,
    140, 897, 672, 288, 312, 860, 724, 226, 884, 508,
    976, 741, 476, 417, 831, 15, 318, 432, 241, 114,
    799, 955, 833, 358, 935, 146, 630, 830, 440, 642,
    356, 373, 271, 715, 367, 393, 190, 669, 8, 861,
    108, 795, 269, 590, 326, 866, 64, 523, 862, 840,
    219, 382, 998, 4, 628, 305, 747, 247, 34, 747,
    729, 645, 856, 974, 24, 568, 24, 694, 608, 480,
    410, 729, 947, 293, 53, 930, 223, 203, 677, 227,
    62, 455, 387, 318, 562, 242, 428, 968,
]

# Certified Values, transcribed verbatim from the StRD header.
CERTIFIED_MEAN = 518.958715596330
CERTIFIED_STDEV = 291.699727470969  # sample standard deviation, denom. = n-1
CERTIFIED_AUTOCORRELATION_LAG1 = -0.120948622967393  # not used by M2 (no autocorr test yet)
