#!/bin/bash

OWNER="your-org-or-username"
REPO="your-repo"
CUTOFF_DATE=$(date -d "2 months ago" +%s)

echo "Deleting unused branches..."

gh api repos/$OWNER/$REPO/branches --paginate \
  | jq -r '.[] | "\(.name) \(.commit.commit.committer.date)"' \
  | while read branch date; do

    COMMIT_DATE=$(date -d "$date" +%s)

    if [[ "$branch" == "main" || "$branch" == "master" || "$branch" == "develop" ]]; then
      continue
    fi

    if [[ $COMMIT_DATE -lt $CUTOFF_DATE ]]; then
      PR_COUNT=$(gh api repos/$OWNER/$REPO/pulls \
        -F head="$OWNER:$branch" \
        -F state=open \
        | jq length)

      if [[ "$PR_COUNT" -eq 0 ]]; then
        echo "Deleting $branch (last commit: $date)"
        gh api -X DELETE repos/$OWNER/$REPO/git/refs/heads/$branch
      fi
    fi
done
