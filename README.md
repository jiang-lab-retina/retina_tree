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

1. Anyone opens **Edit data** and changes nodes or links → **live trees update right away**.
2. **Admin review** compares original vs live, lists every difference, and offers:
   - **Accept all** — copy live → original (changes become permanent)
   - **Reject all** — copy original → live (undo unpublished edits)

Optional: set `app.admin_password` in `.streamlit/secrets.toml` to lock the admin page (see `.streamlit/secrets.toml.example`).

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
4. Optionally add `admin_password` under `[app]` in Secrets.

**Note:** `original_dataset.json` and `working_dataset.json` live on the app filesystem and may reset on redeploy unless you use persistent storage.

## Repository

https://github.com/jiang-lab-retina/retina_tree
