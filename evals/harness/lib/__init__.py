"""Shared library code for the M6 golden-scenario eval harness.

Everything under evals/harness/ runs OUTSIDE the engine package (plain
Python + httpx against the live engine over HTTP) per the build brief --
this package is not sigma_engine and imports nothing from it.
"""
