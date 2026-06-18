import streamlit as st
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables from .env file
# This is how we keep our API key safe — never hardcode it in your code
load_dotenv()

# ── Page configuration ──────────────────────────────────────────
st.set_page_config(
    page_title="My AI Journal",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Welcome screen ───────────────────────────────────────────────
st.title("📓 My AI Growth Journal")
st.markdown("---")

# Get current time to show a relevant greeting
hour = datetime.now().hour
if hour < 12:
    greeting = "Good morning"
elif hour < 17:
    greeting = "Good afternoon"
else:
    greeting = "Good evening"

st.header(f"{greeting}, Yaseen 👋")

st.markdown("""
### What is this?
This is your personal AI-powered journal. It learns about you over time —
your goals, your patterns, your strengths and weaknesses — and becomes
a genuine thinking partner.

### What can you do here?
- 📝 **Journal** — write your daily entries, get AI reflections
- 📊 **Insights** — see your mood, energy and pattern trends over time
- 🎯 **Goals** — set and track your goals, get nudged when you drift
- 🔍 **Ask My Journal** — ask questions about your past entries using AI

### How to get started
👈 Pick any section from the sidebar and start writing.
""")

# ── Sidebar info ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📓 AI Journal")
    st.markdown("---")
    today = datetime.now().strftime("%A, %d %B %Y")
    st.markdown(f"📅 **{today}**")
    st.markdown("---")
    
    # Check if API key is loaded — shows a warning if missing
    if os.getenv("GROQ_API_KEY"):
        st.success("✅ AI Connected")
    else:
        st.error("❌ Groq API key missing — check your .env file")