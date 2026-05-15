#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
lawful-learning-toy bundle placeholder

This bundle declares the Agentplane execution boundary for the calibrated lawful-learning toy examples.
The executable reference implementation lands in SocioProphet/ProCybernetica#23.

A production bundle should vendor or resolve that package before running:
  python -m procyber.lawful_learning.toy
  PYTHONPATH=. python -m pytest -q tests/test_lawful_learning_toy.py
EOF
