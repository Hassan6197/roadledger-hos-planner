#!/usr/bin/env python
"""Vercel-compatible Django entry point for the repository root."""

import os
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "roadledger.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
