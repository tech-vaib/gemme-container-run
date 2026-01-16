#!/bin/bash
source ./config.sh

CUTOFF_DATE=$(date -d "$INACTIVE_DAYS days ago" +%s)

echo "branch,last_commit_date" > "$CSV_FILE"

git fetch --all --prune

git for-each-ref --format='%(refname:short) %(committerdate:iso8601)' refs/remotes/origin |
while read ref date; do
  branch=${ref#origin/}

  [[ "$branch" =~ $PROTECTED_BRANCHES ]] && continue

  COMMIT_TS=$(date -d "$date" +%s)
  [[ $COMMIT_TS -ge $CUTOFF_DATE ]] && continue

  # Check open PRs (unauthenticated)
  PR_COUNT=$(curl -s \
    "$API_URL/repos/$OWNER/$REPO/pulls?state=open&head=$OWNER:$branch" \
    | jq length)

  if [[ "$PR_COUNT" -eq 0 ]]; then
    echo "$branch,$date" >> "$CSV_FILE"
    echo "Unused: $branch | $date"
  fi
done

echo "CSV written to $CSV_FILE"

