📘 README — Update Confluence Release Notes via GitHub Actions
Overview

This repository includes a GitHub Actions workflow that automatically updates a Confluence release notes page whenever a new release tag is created.

The workflow:

Fetches all commit messages and merged PR titles between the previous and current release tags.

Keeps the same order as Git history, with the latest commit first in Confluence.

Skips auto-generated commits like Merge pull request ....

Includes only commits or PRs starting with specific prefixes (e.g., [HIF- or [PLM-).

If the release tag is created from the main branch, the latest commit is excluded from the notes.

Automatically prepends a new release section (with header) to the specified Confluence page.

🧩 Workflow File

The GitHub Action is defined in:
.github/workflows/update-confluence.yml

How It Works

Trigger

The workflow triggers on the event:
on:
  release:
    types: [published]
Whenever a new release tag (e.g., v1.0.0) is published, the workflow starts.
2. Commits and PRs Collection

The workflow finds all commits between the last tag and the current tag.

It pulls commit messages and checks for merged PR titles from the GitHub API.

Filtering and Formatting

Skips commits or PRs with messages like Merge pull request ....

Keeps only commits/PRs starting with [HIF- or [PLM-.

Orders commits from newest → oldest in Confluence.

If the tag is created from the main branch, the latest commit is dropped.

Confluence Update

Builds an HTML section with:
Repo Name: my-repo
Date: 11-03-2025 19:45
Release Tag: v1.2.3
followed by a bullet list of commit messages/PR titles.

Prepends this section to the specified Confluence page.
## Required GitHub Secrets

Before running this workflow, define the following repository secrets under
Settings → Secrets and variables → Actions → New repository secret
| Secret Name            | Description                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------------- |
| `CONFLUENCE_URL`       | Your Confluence base URL (e.g. `https://your-domain.atlassian.net`)                                     |
| `CONFLUENCE_USERNAME`  | Your Confluence username or email                                                                       |
| `CONFLUENCE_API_TOKEN` | API token from Atlassian ([Generate here](https://id.atlassian.com/manage-profile/security/api-tokens)) |
| `CONFLUENCE_PAGE_ID`   | The numeric Confluence page ID to update                                                                |
| `GITHUB_TOKEN`         | Provided automatically by GitHub (no need to create manually)                                           |

Example Output in Confluence

After a new release is published, the Confluence page will automatically update like this:
Repo Name: my-repo
Date: 11-03-2025 20:10
Release Tag: v1.2.3

• [PLM-321] Improve export performance
• [HIF-210] Fix retry logic for API calls
• [PLM-205] Correct currency symbol in invoices

If the tag is created from the main branch, the first item ([PLM-321]) will be excluded.
## Dependencies

The workflow installs and uses the following Python libraries:

atlassian-python-api
requests
esting Tips

To test without publishing an official release:

Manually create a temporary tag and release from a branch other than main.

Verify that your Confluence page updates with the new release notes.

Remove the test section from Confluence if desired.
