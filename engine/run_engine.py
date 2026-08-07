#!/usr/bin/env python3
"""PyInstaller entry script. Kept as a thin top-level script (rather than
`-m sigma_engine.main`) because PyInstaller's dependency analysis wants a
single script file to start from.
"""

from sigma_engine.main import main

if __name__ == "__main__":
    main()
