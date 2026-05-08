#!/usr/bin/env python3
"""MediaClipper Desktop - Entry point."""

import sys
import os

# Ensure bundled tools are found when running as frozen exe
if getattr(sys, "frozen", False):
    _base = os.path.dirname(sys.executable)
    os.environ["PATH"] = os.path.join(_base, "tools", "windows") + os.pathsep + os.environ.get("PATH", "")

from mediaclipper.app import main

if __name__ == "__main__":
    main()
