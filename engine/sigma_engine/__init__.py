"""Sigma AI statistics sidecar (packaging-spike scope: /health and /smoke only).

Version is a plain constant, not read via importlib.metadata: PyInstaller-frozen
binaries don't reliably carry installed-package metadata, so a runtime metadata
lookup is a known way for /health to silently break only in the packaged build.
"""

__version__ = "0.1.0"
