"""Fetch Jira issue D0-1 via the Atlassian MCP integration and print the
required fields.

Usage
-----
Set the three environment variables and run this script::

    export JIRA_BASE_URL=https://myorg.atlassian.net
    export JIRA_USER=user@example.com
    export JIRA_API_TOKEN=<your-api-token>
    python jira_mcp.py

If any variable is missing the script reports **MCP not configured** and
exits with code 1.  Other failure modes (auth / permission / not-found) are
reported with their exact label so the caller can take corrective action.
"""

from __future__ import annotations

import sys

from jira_client import FailureType, JiraClient, JiraIssue, JiraMcpError

_ISSUE_KEY = "D0-1"
_MAX_AC = 3
_MAX_LINKS = 2


def _print_issue(issue: JiraIssue) -> None:
    print(f"Issue key : {issue.key}")
    print(f"Summary   : {issue.summary}")
    print(f"Status    : {issue.status}")
    print(f"Assignee  : {issue.assignee or '(unassigned)'}")

    print("Acceptance criteria (first 3):")
    criteria = issue.acceptance_criteria[:_MAX_AC]
    if criteria:
        for i, criterion in enumerate(criteria, 1):
            print(f"  {i}. {criterion}")
    else:
        print("  (none found)")

    print("Linked issues (first 2):")
    links = issue.linked_issues[:_MAX_LINKS]
    if links:
        for link in links:
            print(f"  [{link.link_type}] {link.key} – {link.summary}")
    else:
        print("  (none found)")


def _failure_label(failure_type: FailureType) -> str:
    labels = {
        FailureType.MCP_NOT_CONFIGURED: "MCP not configured",
        FailureType.AUTHENTICATION_FAILED: "authentication failed",
        FailureType.PERMISSION_DENIED: "permission denied",
        FailureType.ISSUE_NOT_FOUND: "issue not found",
    }
    return labels.get(failure_type, str(failure_type))


def main() -> int:
    try:
        client = JiraClient()
        issue = client.get_issue(_ISSUE_KEY)
        _print_issue(issue)
        return 0
    except JiraMcpError as exc:
        label = _failure_label(exc.failure_type)
        print(f"ERROR: {label}")
        print(f"Detail: {exc.detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
