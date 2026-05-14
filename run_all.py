#!/usr/bin/env python3
import os
import sys
import subprocess

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CODE_DIR = os.path.join(BASE_DIR, "code")
ENTRY = os.path.join(CODE_DIR, "run_all.py")

if __name__ == "__main__":
    if not os.path.exists(ENTRY):
        raise FileNotFoundError(f"Entry script not found: {ENTRY}")
    subprocess.run([sys.executable, ENTRY], check=True)
