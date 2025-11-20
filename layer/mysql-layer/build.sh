#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

rm -rf python
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt -t python

mkdir -p ../../dist
(cd python && zip -r ../../dist/mysql-layer.zip .)
echo "Layer built at dist/mysql-layer.zip"
