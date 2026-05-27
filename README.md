# Retina Trees Viewer

Streamlit app for exploring and editing retina lineage trees. **Edits appear immediately** on the live trees. A separate **original** copy is kept for administrators to **accept** (make permanent) or **reject** (revert the live view).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On first run, `data/original_dataset.json` and `data/working_dataset.json` are created from `data/retina_trees_data.json`.

## How it works

| Copy | File | Purpose |
|------|------|---------|
| **Original** | `data/original_dataset.json` | Last permanently accepted data |
| **Live (working)** | `data/working_dataset.json` | What everyone sees; updated on each edit |

1. Use **Search people** on the home page (fuzzy name/ID match) to jump to someone in the tree — ancestors and descendants expand, match highlighted.
2. Anyone opens **Edit data** and changes nodes or links → **live trees update right away**.
3. **Admin review** compares original vs live, lists every difference, and offers:
   - **Accept all** — copy live → original (changes become permanent)
   - **Reject all** — copy original → live (undo unpublished edits)

Optional: protect **Admin review** with a password (see [Security](#security) below).

## Security

**Do not commit `.streamlit/secrets.toml` to GitHub.** Only `secrets.toml.example` (placeholders) belongs in the repo.

| Where you run the app | How to set the admin password |
|-----------------------|-------------------------------|
| **Local** | `export RETINA_TREE_ADMIN_PASSWORD='…'` then `streamlit run app.py` |
| **Streamlit Cloud** | App **Settings → Secrets** — paste `[app]` / `admin_password` there |

Full details: [SECURITY.md](SECURITY.md)

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
2. Connect the repo at [share.streamlit.io](https://share.streamlit.io).
3. Set **Main file path** to `app.py`.
4. In **Settings → Secrets**, add `admin_password` under `[app]` (do not commit this to GitHub).
5. After each push, use **Manage app → Reboot** so Cloud reinstalls dependencies from `requirements.txt`.

**Requirements:** Streamlit **1.52+** (interactive trees use `st.html` with JavaScript). The repo pins this in `requirements.txt`.

**Blank page?** Open **Manage app → Logs**. Common causes: `KeyError: 'retina_tree.tree_html'` (fixed by using the `rtree` package — do not rename it back to match the repo), or `TypeError` on `st.html` (reboot after upgrading Streamlit). Seed data ships in `data/retina_trees_data.json`; working copies are created on first run.

**Note:** `original_dataset.json` and `working_dataset.json` live on the app filesystem and may reset on redeploy unless you use persistent storage.

## Repository

https://github.com/jiang-lab-retina/retina_tree
