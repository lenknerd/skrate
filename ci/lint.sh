#!/bin/bash
# Simple linting for Python in Skrate app, reformat in-place

# Usage: just run it, no arguments supported


# Go out to base dir of repo
BASEDIR=`git rev-parse --show-toplevel`
cd ${BASEDIR}

# Mypy checks on Python
mypy tests/test_skrate.py
mypy run_skrate  # Includes all other modules

# Check documentation strings in python


# Yapf python formatting checks
yapf -i tests/test_skrate
yapf -i run_skrate
yapf -i skrate/*.py
