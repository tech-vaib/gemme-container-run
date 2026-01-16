#!/bin/bash

OWNER="your-org-or-username"
REPO="your-repo"

INACTIVE_DAYS=60
DRY_RUN=true
REQUIRE_CONFIRM=true

CSV_FILE="unused_branches.csv"

PROTECTED_BRANCHES="^(main|master|develop|release/.*)$"

API_URL="https://api.github.com"

