#!/usr/bin/env bash
# Render the cadence-variance preprint from reports/papers/paper_v1_en.md to PDF.
#
# Mirrors the us_sec_form_nt_late_filing_xs / sec-comment-letter-alpha pipeline:
#   pandoc 3.9 + xelatex (TeX Live) + citeproc + BibTeX
#
# Usage:
#     bash scripts/render-paper.sh         # renders reports/papers/paper_v1_en.pdf
#     bash scripts/render-paper.sh kr      # renders reports/papers/readme_kr.pdf (CJK font)
#
# Prerequisites:
#     - pandoc >= 3.0 (https://pandoc.org/installing.html)
#     - xelatex (TeX Live 2022 or MiKTeX 2024+)
#     - For KR PDF: Malgun Gothic font installed (default on Windows 10+; macOS
#       users can substitute with "Apple SD Gothic Neo")
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PAPERS_DIR="$REPO_ROOT/reports/papers"
TARGET="${1:-en}"

cd "$PAPERS_DIR"

case "$TARGET" in
  en|EN)
    INPUT="paper_v1_en.md"
    OUTPUT="paper_v1_en.pdf"
    EXTRA_OPTS=()
    ;;
  kr|KR)
    INPUT="$REPO_ROOT/readme_kr.md"
    OUTPUT="$REPO_ROOT/readme_kr.pdf"
    EXTRA_OPTS=(
      -V mainfont="Malgun Gothic"
      -V CJKmainfont="Malgun Gothic"
    )
    ;;
  *)
    echo "Usage: $0 [en|kr]" >&2
    exit 1
    ;;
esac

[ -f "$INPUT" ] || { echo "Input not found: $INPUT" >&2; exit 1; }

# refs.bib is required only for the English paper
if [ "$TARGET" = "en" ] || [ "$TARGET" = "EN" ]; then
  [ -f "refs.bib" ] || { echo "BibTeX not found: $PAPERS_DIR/refs.bib" >&2; exit 1; }
  CITE_OPTS=(--citeproc --bibliography=refs.bib)
else
  CITE_OPTS=()
fi

echo "Rendering $INPUT -> $OUTPUT..."
pandoc "$INPUT" \
  -o "$OUTPUT" \
  --pdf-engine=xelatex \
  "${CITE_OPTS[@]}" \
  --number-sections \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V linkcolor=blue \
  "${EXTRA_OPTS[@]}"

echo "Done: $OUTPUT"
ls -la "$OUTPUT"
