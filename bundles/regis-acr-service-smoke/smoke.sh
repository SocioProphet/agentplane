#!/usr/bin/env bash
set -euo pipefail

# Move to Prophet Platform repo
cd ../../prophet-platform

# Run the Regis ACR smoke target via Makefile
make smoke-regis-acr
