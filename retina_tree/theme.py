"""Apple-style design tokens and CSS for the app and embedded tree cards."""

APPLE_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  #MainMenu, footer, header { visibility: hidden; height: 0; }
  .stApp {
    background: #f2f2f4;
    color: #3a3a3c;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", Inter, sans-serif;
  }

  .block-container {
    max-width: 100%;
    padding-top: 1.25rem;
    padding-bottom: 3.5rem;
  }

  /* Let st.html tree blocks expand to content width */
  div[data-testid="stHtml"],
  div[data-testid="stHtml"] > div {
    overflow-x: visible;
    max-width: none;
  }

  h1, h2, h3 {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", Inter, sans-serif;
    letter-spacing: -0.025em;
    font-weight: 600;
    color: #1d1d1f;
  }

  .apple-hero {
    margin-bottom: 1.25rem;
  }

  .apple-hero h1 {
    font-size: clamp(2rem, 4vw, 2.75rem);
    font-weight: 700;
    margin: 0 0 0.35rem;
    line-height: 1.05;
  }

  .apple-hero .subtitle {
    color: #6e6e73;
    font-size: 1.05rem;
    margin: 0;
    font-weight: 400;
    letter-spacing: -0.01em;
  }

  .apple-toolbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    margin-bottom: 1rem;
    padding: 0.65rem 0.85rem;
    background: rgba(255, 255, 255, 0.72);
    backdrop-filter: saturate(180%) blur(20px);
    -webkit-backdrop-filter: saturate(180%) blur(20px);
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 16px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  }

  .apple-toolbar .label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #6e6e73;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .apple-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.7rem;
    border-radius: 999px;
    background: #e8e8ed;
    color: #1d1d1f;
    font-size: 0.82rem;
    font-weight: 500;
  }

  .apple-pill.warn {
    background: #fff4ce;
    color: #8a6d00;
  }

  .apple-section-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #86868b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 0.65rem;
  }

  .apple-card {
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 18px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
    padding: 1.15rem 1.2rem;
    margin-bottom: 1rem;
  }

  .apple-card h3 {
    font-size: 1.05rem;
    margin: 0 0 0.85rem;
  }

  .status-banner {
    border-radius: 12px;
    padding: 0.65rem 0.9rem;
    font-size: 0.92rem;
    margin-top: 0.75rem;
    border: 1px solid transparent;
  }

  .status-banner.success {
    background: #e8f7ee;
    color: #1d6b42;
    border-color: rgba(29, 107, 66, 0.15);
  }

  .status-banner.warning {
    background: #fff8e6;
    color: #8a6d00;
    border-color: rgba(138, 109, 0, 0.15);
  }

  .status-banner.error {
    background: #ffeceb;
    color: #c41e12;
    border-color: rgba(196, 30, 18, 0.15);
  }

  div[data-testid="stButton"] > button {
    border-radius: 8px;
    border: none;
    background: #5a7d8c;
    color: #ffffff;
    font-weight: 500;
    padding: 0.45rem 1rem;
    transition: background 0.2s ease, transform 0.15s ease;
    box-shadow: none;
  }

  div[data-testid="stButton"] > button:hover {
    background: #4a6b78;
    color: #ffffff;
    border: none;
  }

  div[data-testid="stButton"] > button[kind="secondary"] {
    background: #e8e8ed;
    color: #1d1d1f;
  }

  div[data-testid="stButton"] > button[kind="secondary"]:hover {
    background: #dcdce1;
    color: #1d1d1f;
  }

  div[data-testid="stTextInput"] input,
  div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
  div[data-testid="stTextArea"] textarea {
    border-radius: 12px !important;
    border: 1px solid #d2d2d7 !important;
    background: #ffffff !important;
    font-size: 0.95rem !important;
  }

  div[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 16px;
    overflow: hidden;
  }

  [data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(20px);
  }

  a[data-testid="stPageLink-NavLink"] {
    border-radius: 10px;
  }
</style>
"""

APPLE_TREE_CSS = """
:root {
  --paper: #f4f4f5;
  --paper-strong: #fcfcfd;
  --ink: #3a3a3c;
  --muted: #8e8e93;
  --accent: #5a7d8c;
  --accent-strong: #4a6b78;
  --accent-soft: rgba(90, 125, 140, 0.1);
  --branch: #9a9aa1;
  --shadow: rgba(0, 0, 0, 0.04);
  --card-border: #e5e5ea;
  --badge: #ececef;
  --badge-ink: #6e6e73;
}

html, body {
  height: auto;
  min-height: 0;
  margin: 0;
  overflow: visible;
  background: transparent;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased;
}

.tree-card {
  background: var(--paper-strong);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  box-shadow: 0 1px 2px var(--shadow);
  height: fit-content;
  width: 100%;
  overflow: visible;
}

.card-body {
  padding: 0.35rem 0.5rem 0.45rem;
  overflow: visible;
}

.card-head {
  padding: 0.55rem 0.65rem 0.45rem;
  background: #f8f8f9;
  border-bottom: 1px solid #ebebed;
}

.card-title-row {
  margin-bottom: 0.35rem;
}

.card-title-row h2 {
  font-size: 0.92rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--ink);
}

.card-title-row .meta {
  font-size: 0.72rem;
  color: var(--muted);
}

.tree-card.current-box {
  border-color: #c5c5cc;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-toolbar {
  gap: 0.35rem;
}

.card-toolbar button {
  border-radius: 6px;
  border: 1px solid #e0e0e5;
  background: #ffffff;
  color: #5c5c61;
  font-weight: 500;
  font-size: 0.7rem;
  padding: 0.22rem 0.5rem;
}

.card-toolbar button:hover {
  background: #f4f4f6;
  border-color: #d0d0d6;
  color: var(--ink);
  transform: none;
}
"""
