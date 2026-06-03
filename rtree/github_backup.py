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
                "token":   cfg["token"],
                "repo":    cfg["repo"],
                "branch":  cfg.get("branch", "main"),
                "path":    cfg.get("path", "data/retina_trees_data.json"),
                "working_path": cfg.get("working_path", "data/working_backup.json"),
            }
    except Exception:
        pass
    return None


def backup_datasets(
    *,
    accepted_json: str | None = None,
    working_json: str | None = None,
) -> str | None:
    """Push accepted and/or working datasets to GitHub.

    ``accepted_json`` is committed to the seed path (``path``) so it becomes
    the data loaded on a fresh container start. ``working_json`` is committed
    to ``working_path`` so pending (not-yet-accepted) edits also survive.

    Returns ``None`` on success (or when nothing to do), else an error string.
    Returns a sentinel message if GitHub is not configured.
    """
    cfg = load_github_config()
    if cfg is None:
        return "GitHub backup not configured."

    errors: list[str] = []
    if accepted_json is not None:
        err = push_dataset_to_github(
            accepted_json,
            token=cfg["token"],
            repo=cfg["repo"],
            branch=cfg["branch"],
            path=cfg["path"],
            commit_message="chore: auto-backup accepted dataset [skip ci]",
        )
        if err:
            errors.append(err)
    if working_json is not None:
        err = push_dataset_to_github(
            working_json,
            token=cfg["token"],
            repo=cfg["repo"],
            branch=cfg["branch"],
            path=cfg["working_path"],
            commit_message="chore: auto-backup working edits [skip ci]",
        )
        if err:
            errors.append(err)

    return " ; ".join(errors) if errors else None
