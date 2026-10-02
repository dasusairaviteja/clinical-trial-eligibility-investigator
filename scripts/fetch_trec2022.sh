#!/usr/bin/env bash
# Fetch TREC 2022 Clinical Trials benchmark files (public, no login required).
# Usage: ./scripts/fetch_trec2022.sh [dest_dir]
set -euo pipefail
DEST="${1:-data/trec2022}"
mkdir -p "$DEST"
curl -sSL -o "$DEST/topics2022.xml" https://trec.nist.gov/data/trials/topics2022.xml
curl -sSL -o "$DEST/qrels2022.txt" https://trec.nist.gov/data/trials/qrels2022.txt
echo "TREC 2022 files downloaded to $DEST:"
ls -la "$DEST"/topics2022.xml "$DEST"/qrels2022.txt
