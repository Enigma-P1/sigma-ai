#!/usr/bin/env bash
# Phase 3 — hand each model its OWN run back and get the write-up.
#
#   phase3.sh <persona-dir> <provider> <model> <out.md> [max_images]
#
# The model sees: the plan it wrote in phase 1, the driver's factual log of
# what actually happened, and the screenshots from its own run. It does not
# see the other persona's run, and it does not see any of my commentary.
set -euo pipefail

DIR="$1"; PROVIDER="$2"; MODEL="$3"; OUT="$4"; MAXIMG="${5:-24}"
WHO="$(basename "$DIR")"
SO=/home/user/Personal-AI/tools/second-opinion/second_opinion.py

MATERIAL="/tmp/uat/$WHO-material.md"
{
  echo "# What you said you would do"
  echo
  cat "/tmp/uat/$WHO-plan.md"
  echo
  echo "# What actually happened when someone did it for you"
  echo
  cat "$DIR/RUN-LOG.md"
  echo
  echo "# The raw step-by-step log, including every word that was on the screen"
  echo
  for f in "$DIR"/transcript-*.md; do
    [ -f "$f" ] && grep -v '^!\[' "$f"
  done
} > "$MATERIAL"

# Spread the screenshots across the whole run rather than taking the first N
# alphabetically -- `head` would send only the opening chunks and none of the
# charts, reports or the reopen at the end.
ALL=("$DIR"/shots/*.png)
TOTAL=${#ALL[@]}
STEP=$(( (TOTAL + MAXIMG - 1) / MAXIMG )); [ "$STEP" -lt 1 ] && STEP=1
SHOTS=()
for ((i=0; i<TOTAL; i+=STEP)); do SHOTS+=("${ALL[$i]}"); done
IMGARGS=()
for s in "${SHOTS[@]}"; do IMGARGS+=(--image "$s"); done

echo "material: $(wc -l < "$MATERIAL") lines; images: ${#SHOTS[@]}"

case "$PROVIDER" in
  openai) MODELFLAG=(--openai-model "$MODEL") ;;
  xai)    MODELFLAG=(--xai-model "$MODEL") ;;
  *) echo "unknown provider $PROVIDER"; exit 1 ;;
esac

python3 "$SO" \
  --providers "$PROVIDER" "${MODELFLAG[@]}" \
  --mode answer --max-tokens 24000 \
  --system-file /tmp/uat/phase3-system.txt \
  --file "$MATERIAL" \
  "${IMGARGS[@]}" \
  --intent "$(cat /tmp/uat/phase3-intent.txt)" \
  --no-save > "$OUT" 2>&1

echo "wrote $OUT ($(wc -l < "$OUT") lines)"
