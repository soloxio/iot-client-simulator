"""Thin Atlassian Jira REST v3 client with MCP-style error categorisation.

Failure types (mirrors the Atlassian MCP error taxonomy):
  - mcp-not-configured   : credentials / base-URL absent; cannot even attempt a call
  - authentication-failed: 401 – credentials present but rejected
  - permission-denied    : 403 – authenticated but not authorised for this resource
  - issue-not-found      : 404 – issue key does not exist in the project
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import requests


class FailureType(str, Enum):
    MCP_NOT_CONFIGURED = "mcp-not-configured"
    AUTHENTICATION_FAILED = "authentication-failed"
    PERMISSION_DENIED = "permission-denied"
    ISSUE_NOT_FOUND = "issue-not-found"


class JiraMcpError(Exception):
    """Raised when a Jira MCP operation cannot be completed."""

    def __init__(self, failure_type: FailureType, detail: str = "") -> None:
        self.failure_type = failure_type
        self.detail = detail
        super().__init__(f"[{failure_type.value}] {detail}")


@dataclass
class LinkedIssue:
    key: str
    summary: str
    link_type: str


@dataclass
class JiraIssue:
    key: str
    summary: str
    status: str
    assignee: str | None
    acceptance_criteria: list[str] = field(default_factory=list)
    linked_issues: list[LinkedIssue] = field(default_factory=list)


class JiraClient:
    """Minimal Jira REST v3 client driven by environment variables.

    Required environment variables
    ------------------------------
    JIRA_BASE_URL   e.g. ``https://myorg.atlassian.net``
    JIRA_USER       Atlassian account e-mail
    JIRA_API_TOKEN  API token from https://id.atlassian.com/manage-profile/security/api-tokens
    """

    _ENV_BASE_URL = "JIRA_BASE_URL"
    _ENV_USER = "JIRA_USER"
    _ENV_TOKEN = "JIRA_API_TOKEN"

    def __init__(self) -> None:
        base_url = os.environ.get(self._ENV_BASE_URL, "").strip()
        user = os.environ.get(self._ENV_USER, "").strip()
        token = os.environ.get(self._ENV_TOKEN, "").strip()

        if not (base_url and user and token):
            missing = [
                v
                for v, val in (
                    (self._ENV_BASE_URL, base_url),
                    (self._ENV_USER, user),
                    (self._ENV_TOKEN, token),
                )
                if not val
            ]
            raise JiraMcpError(
                FailureType.MCP_NOT_CONFIGURED,
                f"Missing environment variable(s): {', '.join(missing)}. "
                "Set JIRA_BASE_URL, JIRA_USER, and JIRA_API_TOKEN to enable "
                "Atlassian MCP access.",
            )

        self._base_url = base_url.rstrip("/")
        self._auth = (user, token)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_issue(self, issue_key: str) -> JiraIssue:
        """Fetch a Jira issue and return a structured :class:`JiraIssue`.

        Parameters
        ----------
        issue_key:
            Jira issue key, e.g. ``"D0-1"``.

        Raises
        ------
        JiraMcpError
            With the appropriate :class:`FailureType` on any error.
        """
        data = self._fetch_issue_json(issue_key)
        return self._parse(data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_issue_json(self, issue_key: str) -> dict[str, Any]:
        url = f"{self._base_url}/rest/api/3/issue/{issue_key}"
        try:
            response = requests.get(
                url,
                auth=self._auth,
                headers={"Accept": "application/json"},
                timeout=15,
            )
        except requests.RequestException as exc:
            # Network errors mean the integration cannot reach Jira at all,
            # which is functionally equivalent to the MCP not being configured
            # (wrong base URL, no connectivity, firewall, etc.).
            raise JiraMcpError(
                FailureType.MCP_NOT_CONFIGURED,
                f"Cannot reach Jira at {self._base_url} – check JIRA_BASE_URL "
                f"and network connectivity. Underlying error: {exc}",
            ) from exc

        if response.status_code == 401:
            raise JiraMcpError(
                FailureType.AUTHENTICATION_FAILED,
                "Jira rejected the supplied credentials (HTTP 401). "
                "Check JIRA_USER and JIRA_API_TOKEN.",
            )
        if response.status_code == 403:
            raise JiraMcpError(
                FailureType.PERMISSION_DENIED,
                f"Authenticated but not authorised to read {issue_key} (HTTP 403).",
            )
        if response.status_code == 404:
            raise JiraMcpError(
                FailureType.ISSUE_NOT_FOUND,
                f"Issue {issue_key!r} was not found in Jira (HTTP 404).",
            )
        if not response.ok:
            # Unexpected status codes (e.g. 500 / 502 / 503) indicate the Jira
            # service is unhealthy or the base URL points to the wrong host.
            # Mapped to MCP_NOT_CONFIGURED because the integration cannot be
            # used in its current state (the problem statement defines only the
            # four failure types: not-configured / auth / permission / not-found).
            raise JiraMcpError(
                FailureType.MCP_NOT_CONFIGURED,
                f"Jira returned HTTP {response.status_code} (server or proxy error) "
                f"for {issue_key}. Verify JIRA_BASE_URL. "
                f"Response: {response.text[:200]}",
            )

        return response.json()

    @staticmethod
    def _parse(data: dict[str, Any]) -> JiraIssue:
        fields: dict[str, Any] = data.get("fields", {})

        # --- assignee ---
        assignee_obj = fields.get("assignee") or {}
        assignee = assignee_obj.get("displayName") or assignee_obj.get("name")

        # --- acceptance criteria ---
        # Commonly stored in a custom field named "Acceptance Criteria" or
        # in the description document.  We check the custom field first.
        raw_ac = (
            fields.get("customfield_acceptance_criteria")
            or fields.get("customfield_10016")  # common AC field id
            or ""
        )
        if isinstance(raw_ac, dict):
            # Atlassian Document Format – extract plain text from paragraphs
            raw_ac = _extract_adf_text(raw_ac)
        acceptance_criteria = _parse_criteria_lines(str(raw_ac)) if raw_ac else []

        # --- linked issues ---
        links_raw: list[dict] = fields.get("issuelinks", [])
        linked: list[LinkedIssue] = []
        for link in links_raw:
            link_type = link.get("type", {}).get("name", "")
            for direction in ("inwardIssue", "outwardIssue"):
                target = link.get(direction)
                if target:
                    linked.append(
                        LinkedIssue(
                            key=target.get("key", ""),
                            summary=target.get("fields", {}).get("summary", ""),
                            link_type=link_type,
                        )
                    )

        return JiraIssue(
            key=data.get("key", ""),
            summary=fields.get("summary", ""),
            status=fields.get("status", {}).get("name", ""),
            assignee=assignee,
            acceptance_criteria=acceptance_criteria,
            linked_issues=linked,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_adf_text(doc: dict) -> str:
    """Recursively extract plain text from an Atlassian Document Format node."""
    parts: list[str] = []
    if doc.get("type") == "text":
        parts.append(doc.get("text", ""))
    for child in doc.get("content", []):
        parts.append(_extract_adf_text(child))
    return "\n".join(filter(None, parts))


def _parse_criteria_lines(text: str) -> list[str]:
    """Split multi-line acceptance-criteria text into individual criteria."""
    lines = [line.strip().lstrip("-*•·").strip() for line in text.splitlines()]
    return [line for line in lines if line]
