"""Apple-style design tokens and CSS for the app and embedded tree cards."""

APPLE_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  #MainMenu, footer, header { visibility: hidden; height: 0; }
  .stApp {
    background: #f5f5f7;
    color: #1d1d1f;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", Inter, sans-serif;
  }

  .block-container {
    max-width: 1200px;
    padding-top: 1.25rem;
    padding-bottom: 3.5rem;
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
    border-radius: 980px;
    border: none;
    background: #0071e3;
    color: #ffffff;
    font-weight: 500;
    padding: 0.45rem 1rem;
    transition: background 0.2s ease, transform 0.15s ease;
    box-shadow: none;
  }

  div[data-testid="stButton"] > button:hover {
    background: #0077ed;
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
  --paper: #f5f5f7;
  --paper-strong: #ffffff;
  --ink: #1d1d1f;
  --muted: #6e6e73;
  --accent: #0071e3;
  --accent-strong: #0077ed;
  --accent-soft: rgba(0, 113, 227, 0.08);
  --warning: #8a6d00;
  --warning-bg: #fff8e6;
  --error: #c41e12;
  --error-bg: #ffeceb;
  --success: #1d6b42;
  --success-bg: #e8f7ee;
  --branch: #d2d2d7;
  --shadow: rgba(0, 0, 0, 0.06);
  --card-border: rgba(0, 0, 0, 0.06);
  --badge: #e8e8ed;
  --badge-ink: #424245;
}

html, body {
  height: auto;
  min-height: 0;
  margin: 0;
  overflow: visible;
  background: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", sans-serif;
}

.tree-card {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 18px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  height: fit-content;
  width: 100%;
}

.card-body {
  padding: 0.5rem 0.65rem 0.65rem;
  overflow: visible;
}

.forest {
  padding: 0.15rem 0.2rem 0.3rem;
}

.root-list {
  gap: 0.55rem 0.75rem;
}

.card-head {
  padding: 0.75rem 0.85rem 0.65rem;
}

.card-title-row {
  margin-bottom: 0.5rem;
}

.tree-card.current-box {
  border-color: rgba(0, 113, 227, 0.35);
  box-shadow: 0 4px 20px rgba(0, 113, 227, 0.12);
}

.card-head {
  background: linear-gradient(180deg, rgba(0, 113, 227, 0.04), transparent), #ffffff;
}

.card-title-row h2 {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.card-toolbar button {
  border-radius: 980px;
  border: none;
  background: #e8e8ed;
  color: #1d1d1f;
  font-weight: 500;
  font-size: 0.8rem;
  padding: 0.38rem 0.72rem;
}

.card-toolbar button:hover {
  background: #dcdce1;
  transform: none;
}

.node-button,
.node-leaf {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  font-weight: 500;
  font-size: 0.88rem;
}

.node-button:hover {
  background: #f5f5f7;
  border-color: rgba(0, 113, 227, 0.25);
}

.root-list > .tree-node > .node-row .node-button,
.root-list > .tree-node > .node-row .node-leaf {
  background: linear-gradient(180deg, #ffffff, #f5f5f7);
  border-color: rgba(0, 113, 227, 0.2);
  font-weight: 600;
}

.caret {
  color: #0071e3;
}

.shared-badge {
  background: #e8e8ed;
  color: #424245;
  font-weight: 600;
}
"""
