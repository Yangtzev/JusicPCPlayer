# SPDX-License-Identifier: GPL-3.0-only
"""Packaged theme-client entry point."""
import os
from jusic_gui_bootstrap import main

if __name__ == "__main__":
    if os.environ.get("JUSIC_BUILD_SMOKE_CHECK"):
        from tools import frozen_smoke_check
    else:
        main()
