# Retina Trees Viewer

Streamlit app for exploring and editing retina lineage trees from JSON linkage data. The interface follows the original [retina_trees_viewer.html](https://github.com/jiang-lab-retina/retina_tree) layout: collapsible hierarchical trees, per-box cards, and a built-in JSON editor.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On startup the app loads `data/retina_trees_data.json` automatically and shows all lineage trees on the home page. Use **Edit data** (separate page) to modify nodes and links.

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

## Repository

https://github.com/jiang-lab-retina/retina_tree
