"""NIST StRD reference dataset for stats-core reference tests (M2).

Source: NIST Statistical Reference Datasets (StRD), Univariate Summary
Statistics collection, "Lower Level of Difficulty" dataset "Mavro"
(filter transmittance data, Radu Mavrodineaunu, NIST chemistry staff):
https://www.itl.nist.gov/div898/strd/univ/data/Mavro.dat

Fetched live in-container on 2026-08-07: DATA below was transcribed from
that file's 50-observation data section (lines 61-110), and
CERTIFIED_MEAN / CERTIFIED_STDEV / CERTIFIED_AUTOCORRELATION were
transcribed verbatim from its "Certified Values" header (lines 41-43).
Recomputing mean/stdev over DATA reproduces the certified figures to
within 1e-9 relative tolerance (see tests/test_stats_descriptive.py) --
the transcription is self-verifying, not just copied by hand. This
dataset's much smaller spread (values cluster near 2.0018) than Lew or
Lottery makes it a useful second, differently-scaled cross-check.
"""

DATASET_NAME = "Mavro"

# 50 observations, NIST StRD Mavro.dat lines 61-110.
DATA: list[float] = [
    2.00180, 2.00170, 2.00180, 2.00190, 2.00180, 2.00170, 2.00150, 2.00140, 2.00150, 2.00150,
    2.00170, 2.00180, 2.00180, 2.00190, 2.00190, 2.00210, 2.00200, 2.00160, 2.00140, 2.00130,
    2.00130, 2.00150, 2.00150, 2.00160, 2.00150, 2.00140, 2.00130, 2.00140, 2.00150, 2.00140,
    2.00150, 2.00160, 2.00150, 2.00160, 2.00190, 2.00200, 2.00200, 2.00210, 2.00220, 2.00230,
    2.00240, 2.00250, 2.00270, 2.00260, 2.00260, 2.00260, 2.00270, 2.00260, 2.00250, 2.00240,
]

# Certified Values, transcribed verbatim from the StRD header.
CERTIFIED_MEAN = 2.00185600000000
CERTIFIED_STDEV = 0.000429123454003053  # sample standard deviation, denom. = n-1
CERTIFIED_AUTOCORRELATION_LAG1 = 0.937989183438248  # not used by M2 (no autocorr test yet)
