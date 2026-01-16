#!/bin/bash
source ./config.sh

if [[ "$DRY_RUN" == true ]]; then
  echo "DRY RUN — no deletion"
  cat "$CSV_FILE"
  exit 0
fi

if [[ "$REQUIRE_CONFIRM" == true ]]; then
  read -p "Type DELETE to confirm branch deletion: " CONFIRM
  [[ "$CONFIRM" != "DELETE" ]] && echo "Aborted." && exit 0
fi

tail -n +2 "$CSV_FILE" | while IFS=',' read branch date; do
  echo "Deleting $branch"
  git push origin --delete "$branch"
done

