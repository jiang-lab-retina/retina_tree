"""Push the accepted dataset back to GitHub so it survives redeployments.

Requires a GitHub personal access token (classic or fine-grained with
"Contents: Read and Write" on the repo) stored as a Streamlit secret:

    # .streamlit/secrets.toml (local) or Streamlit Cloud → App settings → Secrets
    [github]
    token = "github_pat_..."
    repo  = "jiang-lab-retina/retina_tree"          # owner/repo
    branch = "main"
    path  = "data/retina_trees_data.json"            # file to overwrite in repo

All four keys are required.  If any are missing the backup is silently
skipped (returns an error string instead of raising).
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request


def _api(
    path: str,
    *,
    token: str,
    method: str = "GET",
    body: dict | None = None,
) -> dict:
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def push_dataset_to_github(
    content: str,
    *,
    token: str,
    repo: str,
    branch: str = "main",
    path: str = "data/retina_trees_data.json",
    commit_message: str = "chore: auto-backup accepted dataset [skip ci]",
) -> str | None:
    """Write *content* (JSON string) to *path* on GitHub.

    Returns ``None`` on success, or an error message string on failure.
    """
    if not token or not repo:
        return "GitHub token or repo not configured."

    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

    # Fetch current SHA so GitHub allows the update.
    try:
        current = _api(f"/repos/{repo}/contents/{path}?ref={branch}", token=token)
        sha: str | None = current.get("sha")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            sha = None  # file doesn't exist yet — create it
        else:
            return f"GitHub API error fetching file: {exc.code} {exc.reason}"
    except Exception as exc:
        return f"Error contacting GitHub: {exc}"

    body: dict = {
        "message": commit_message,
        "content": encoded,
        "branch": branch,
    }
    if sha:
        body["sha"] = sha

    try:
        _api(f"/repos/{repo}/contents/{path}", token=token, method="PUT", body=body)
        return None  # success
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return f"GitHub API error pushing file: {exc.code} — {detail}"
    except Exception as exc:
        return f"Error pushing to GitHub: {exc}"


def load_github_config() -> dict[str, str] | None:
    """Return the [github] secret block, or None if not configured."""
    try:
        import streamlit as st
        cfg = st.secrets.get("github", {})
        if cfg.get("token") and cfg.get("repo"):
            return {
                "token":  cfg["token"],
                "repo":   cfg["repo"],
                "branch": cfg.get("branch", "main"),
                "path":   cfg.get("path", "data/retina_trees_data.json"),
            }
    except Exception:
        pass
    return None
