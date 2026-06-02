CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #f7f8fb;
  --panel: rgba(255,255,255,0.82);
  --ink: #111827;
  --muted: #5b6475;
  --blue: #2563eb;
  --teal: #14b8a6;
  --amber: #f59e0b;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
  background:
    radial-gradient(circle at 10% 0%, rgba(20,184,166,.12), transparent 28%),
    radial-gradient(circle at 85% 12%, rgba(245,158,11,.12), transparent 25%),
    linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
  color: var(--ink);
}
.main .block-container { max-width: 1220px; padding-top: 1.25rem; padding-bottom: 3rem; }
.hero {
  min-height: 78vh;
  display: grid;
  align-items: center;
  padding: 3rem 0 1.5rem;
}
.hero h1 {
  font-size: clamp(3rem, 6vw, 5.8rem);
  line-height: .92;
  letter-spacing: 0;
  margin: 0 0 1rem;
  color: #0f172a;
}
.hero p { max-width: 680px; color: var(--muted); font-size: 1.22rem; line-height: 1.7; }
.premium-card {
  background: var(--panel);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(148, 163, 184, .35);
  border-radius: 8px;
  padding: 1.05rem;
  box-shadow: 0 20px 60px rgba(15, 23, 42, .08);
}
.gradient-card {
  background: linear-gradient(135deg, rgba(37,99,235,.94), rgba(20,184,166,.88));
  color: white;
  border-radius: 8px;
  padding: 1rem;
  min-height: 120px;
}
.metric-title { color: #64748b; font-size: .82rem; text-transform: uppercase; font-weight: 700; }
.metric-value { font-size: 2rem; font-weight: 800; color: #0f172a; }
.newspaper {
  background: #fffdf6;
  border: 1px solid #e7dfca;
  border-radius: 8px;
  padding: 1rem;
  font-family: Georgia, serif;
}
.timeline-dot {
  width: 10px;
  height: 10px;
  background: var(--blue);
  border-radius: 999px;
  display: inline-block;
  margin-right: .5rem;
}
.chat-optimistic, .chat-skeptical {
  border-radius: 8px;
  padding: .85rem 1rem;
  margin: .55rem 0;
}
.chat-optimistic { background: rgba(20,184,166,.14); border-left: 4px solid var(--teal); }
.chat-skeptical { background: rgba(245,158,11,.16); border-left: 4px solid var(--amber); }
.small-muted { color: var(--muted); font-size: .9rem; }
.stButton > button, .stDownloadButton > button {
  border-radius: 8px;
  font-weight: 700;
}
textarea, input { border-radius: 8px !important; }
section[data-testid="stSidebar"] { background: rgba(255,255,255,.7); }
</style>
"""

