import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from textblob import TextBlob
import sqlite3
import os
from datetime import datetime

load_dotenv()

# ── Page config ──────────────────────────────────────────────────
st.set_page_config(page_title="Journal", page_icon="📝", layout="wide")
st.title("📝 Daily Journal")
st.markdown("Write freely. No rules, no format. Just you.")
st.markdown("---")

# ── Database setup ───────────────────────────────────────────────
# SQLite is a lightweight local database — perfect for storing your entries
# Think of it as a smart Excel file that lives in your data/ folder
def init_db():
    conn = sqlite3.connect("data/journal.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            entry TEXT,
            mood_score REAL,
            mood_label TEXT,
            energy_score REAL,
            ai_reflection TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ── Sentiment analysis ───────────────────────────────────────────
# TextBlob reads your text and returns a polarity score
# -1.0 = very negative, 0 = neutral, +1.0 = very positive
def analyze_mood(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity      # mood: -1 to +1
    subjectivity = blob.sentiment.subjectivity  # energy proxy: 0 to 1

    # Convert raw score to a human label
    if polarity >= 0.3:
        mood_label = "😊 Positive"
    elif polarity <= -0.3:
        mood_label = "😔 Low"
    else:
        mood_label = "😐 Neutral"

    return polarity, mood_label, subjectivity

# ── AI reflection via Groq ───────────────────────────────────────
# This is where LangChain + Groq come in
# We send your entry to LLaMA 3 with a carefully designed system prompt
# The system prompt is what makes the AI respond like a growth coach
# not like a generic chatbot
def get_ai_reflection(entry_text, mood_label):
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",  # free, fast LLaMA 3 model on Groq
        temperature=0.7  # 0 = very predictable, 1 = more creative
    )

    system_prompt = """You are Yaseen's personal growth companion. You know he is a CS graduate from Lahore, Pakistan, actively job hunting for ML/Data Science roles, wants to move abroad, and is building his skills while dealing with the uncertainty of being between jobs.

When he writes a journal entry, respond like a trusted friend who is also a thoughtful coach:
1. Acknowledge what he's actually feeling — directly and honestly, no sugarcoating
2. Point out one pattern or blind spot you notice in his thinking
3. Give one concrete, specific next action he can take today — not vague advice
4. End with one sharp question that challenges him to think deeper

Rules:
- Talk TO him directly, use "you" not "these words" or "the entry"
- Be warm but real. No toxic positivity, no corporate language
- Keep it under 150 words
- Never start with "I" or "Great entry!"
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Journal entry (mood: {mood_label}):\n\n{entry_text}")
    ]

    response = llm.invoke(messages)
    return response.content

# ── Save entry to database ───────────────────────────────────────
def save_entry(entry, mood_score, mood_label, energy_score, ai_reflection):
    conn = sqlite3.connect("data/journal.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO entries 
        (date, entry, mood_score, mood_label, energy_score, ai_reflection, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d"),
        entry,
        mood_score,
        mood_label,
        energy_score,
        ai_reflection,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

# ── UI ───────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Today's Entry")
    entry_text = st.text_area(
        label="What's on your mind?",
        placeholder="Write about your day, your thoughts, what went well, what didn't, what you're working towards...",
        height=300,
        label_visibility="collapsed"
    )

    submit = st.button("💾 Save & Reflect", type="primary", use_container_width=True)

with col2:
    st.subheader("Today")
    st.markdown(f"📅 {datetime.now().strftime('%A, %d %B %Y')}")
    st.markdown("---")
    st.markdown("**Tips for better entries:**")
    st.markdown("""
    - Write at least 3-4 sentences
    - Mention what you're working on
    - Include how you're feeling and why
    - Note one win, however small
    """)

# ── On submit ────────────────────────────────────────────────────
if submit:
    if len(entry_text.strip()) < 20:
        st.warning("Write a bit more — at least a sentence or two.")
    else:
        with st.spinner("Reading your entry and thinking..."):
            # Step 1: analyze mood
            mood_score, mood_label, energy_score = analyze_mood(entry_text)

            # Step 2: get AI reflection
            ai_reflection = get_ai_reflection(entry_text, mood_label)

            # Step 3: save everything
            save_entry(entry_text, mood_score, mood_label, energy_score, ai_reflection)

        # Show results
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        with col3:
            st.metric("Mood", mood_label)
        with col4:
            st.metric("Energy", f"{round(energy_score * 100)}%")

        st.markdown("### 🤖 AI Reflection")
        st.info(ai_reflection)
        st.success("Entry saved ✅")

# ── Recent entries ───────────────────────────────────────────────
st.markdown("---")
st.subheader("Recent Entries")

conn = sqlite3.connect("data/journal.db")
cursor = conn.cursor()
cursor.execute("SELECT date, entry, mood_label, ai_reflection FROM entries ORDER BY created_at DESC LIMIT 5")
rows = cursor.fetchall()
conn.close()

if rows:
    for row in rows:
        with st.expander(f"📅 {row[0]} — {row[2]}"):
            st.markdown("**Your entry:**")
            st.write(row[1])
            st.markdown("**AI reflection:**")
            st.info(row[3])
else:
    st.info("No entries yet. Write your first one above ☝️")