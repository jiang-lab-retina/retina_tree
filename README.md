# Retina Trees Viewer

Streamlit app for exploring retina lineage trees from JSON linkage data. The home page shows **approved** trees; contributors sign in with **Google**, submit tracked edits, and **administrators** approve changes before they go live.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with Google OAuth credentials and admin emails
streamlit run app.py
```

On first run, `data/approved_dataset.json` is created from `data/retina_trees_data.json`.

## Google sign-in setup

1. In [Google Cloud Console](https://console.cloud.google.com/), create an **OAuth 2.0 Client ID** (Web application).
2. Add authorized redirect URI:
   - Local: `http://localhost:8501/oauth2callback`
   - Streamlit Cloud: `https://<your-app>.streamlit.app/oauth2callback`
3. Copy Client ID and Client Secret into `.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`).
4. Set `app.admin_emails` to the Google accounts that may approve edits.

Requires **Streamlit ≥ 1.42** (`st.login` / OIDC).

### Local dev without Google

Set `app.allow_dev_login = true` in `secrets.toml` and leave OAuth blank to use email-only dev sign-in (not for production).

## Workflow

| Role | What they do |
|------|----------------|
| **Visitor** | Browse approved trees on the home page |
| **Contributor** | Sign in → **Propose edit** → submit node/link changes (tracked in SQLite) |
| **Administrator** | **Admin review** → approve (publishes to `approved_dataset.json`) or reject with a note |

Contributors see status of their submissions on the edit page. Admins see a pending queue and recent history.

## Data format

Each dataset file contains:

- `version` — schema version (currently `1`)
- `title` — display title
- `boxes` — list of tree panels, each with:
  - `id`, `title`
  - `nodes` — array of `{ "id", "label", ... }` (optional `pubmed` metadata is preserved)
  - `links` — array of `[parent_id, child_id]` pairs

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Open [share.streamlit.io](https://share.streamlit.io) and connect the repo.
3. Set **Main file path** to `app.py`.
4. Add secrets from `.streamlit/secrets.toml.example` (use your production `redirect_uri`).

**Note:** Streamlit Cloud filesystem is ephemeral. `data/proposals.db` and `data/approved_dataset.json` reset on redeploy unless you use persistent storage or an external database. For production, plan to back up approved JSON or attach external storage.

## Repository

https://github.com/jiang-lab-retina/retina_tree
