# Security

## Secrets must not be in GitHub

| File | Commit to GitHub? |
|------|-------------------|
| `.streamlit/secrets.toml.example` | Yes — placeholders only |
| `.streamlit/secrets.toml` | **Never** — real passwords |
| `.env` | **Never** |

This repository lists `.streamlit/secrets.toml` and `.env` in `.gitignore`. CI also fails if `secrets.toml` is accidentally committed.

## Where to put the admin password

**Streamlit Community Cloud (recommended for deploy)**

1. Open your app on [share.streamlit.io](https://share.streamlit.io).
2. **Settings → Secrets**.
3. Add:

```toml
[app]
admin_password = "your-strong-random-password"
```

Secrets stay on Streamlit’s servers, not in the public repo.

**Local development (recommended)**

```bash
export RETINA_TREE_ADMIN_PASSWORD='your-strong-random-password'
streamlit run app.py
```

**Local development (alternative)**

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml locally only — never git add or push it
```

## If you already pushed a real `secrets.toml`

1. **Rotate the password immediately** (treat the old one as public).
2. Remove the file from git history (example with [git-filter-repo](https://github.com/newren/git-filter-repo)):

```bash
git filter-repo --path .streamlit/secrets.toml --invert-paths
git push --force origin main
```

3. On Streamlit Cloud, update Secrets with the new password.
4. Revoke any other credentials that were in that file (OAuth client secrets, API keys, etc.).

## Current app risk model

- Tree **editing** is open to anyone with the app URL.
- **Admin review** is optional; set `RETINA_TREE_ADMIN_PASSWORD` or Streamlit `[app] admin_password` to restrict accept/reject.
- Dataset files on disk are not secret; protect the deployed app URL and admin password if you need tighter control.
