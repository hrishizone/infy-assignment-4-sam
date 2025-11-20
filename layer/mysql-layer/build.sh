#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

rm -rf python
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt -t python

# Create dist/ at the repo root
mkdir -p ../../dist

# Zip the "python" folder into repo_root/dist/mysql-layer.zip
zip -r ../../dist/mysql-layer.zip python

echo "Layer built at ../../dist/mysql-layer.zip"
