import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter
import re

st.set_page_config(page_title="Insights", page_icon="📊", layout="wide")
st.title("📊 My Insights")
st.markdown("Patterns in your thinking, mood and energy over time.")
st.markdown("---")

# ── Load all entries from database ───────────────────────────────
def load_entries():
    conn = sqlite3.connect("data/journal.db")
    df = pd.read_sql_query(
        "SELECT * FROM entries ORDER BY created_at ASC", conn
    )
    conn.close()
    return df

df = load_entries()

if df.empty:
    st.info("No entries yet. Write a few journal entries first and come back here.")
    st.stop()

# Convert date column to proper datetime format
df["date"] = pd.to_datetime(df["date"])
df["mood_score"] = df["mood_score"].astype(float)
df["energy_score"] = df["energy_score"].astype(float)

# ── Summary metrics at the top ───────────────────────────────────
st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Entries", len(df))
with col2:
    avg_mood = df["mood_score"].mean()
    mood_label = "😊 Positive" if avg_mood > 0.1 else "😔 Low" if avg_mood < -0.1 else "😐 Neutral"
    st.metric("Average Mood", mood_label)
with col3:
    avg_energy = df["energy_score"].mean()
    st.metric("Average Energy", f"{round(avg_energy * 100)}%")
with col4:
    streak = len(df["date"].unique())
    st.metric("Days Journaled", streak)

st.markdown("---")

# ── Mood over time ───────────────────────────────────────────────
st.subheader("Mood Over Time")
st.caption("How your mood has shifted across your entries. Above 0 = positive, below 0 = low.")

fig_mood = px.line(
    df,
    x="date",
    y="mood_score",
    markers=True,
    line_shape="spline",
    color_discrete_sequence=["#7C3AED"]
)
fig_mood.add_hline(
    y=0,
    line_dash="dash",
    line_color="gray",
    annotation_text="Neutral"
)
fig_mood.update_layout(
    xaxis_title="Date",
    yaxis_title="Mood Score",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(range=[-1, 1])
)
st.plotly_chart(fig_mood, use_container_width=True)

# ── Energy over time ─────────────────────────────────────────────
st.subheader("Energy Over Time")
st.caption("How engaged and expressive your writing has been. Higher = more energetic entries.")

fig_energy = px.area(
    df,
    x="date",
    y="energy_score",
    line_shape="spline",
    color_discrete_sequence=["#059669"]
)
fig_energy.update_layout(
    xaxis_title="Date",
    yaxis_title="Energy Score",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(range=[0, 1])
)
st.plotly_chart(fig_energy, use_container_width=True)

# ── Mood distribution ────────────────────────────────────────────
st.subheader("Mood Distribution")
st.caption("How often you've been in each mood state.")

mood_counts = df["mood_label"].value_counts().reset_index()
mood_counts.columns = ["Mood", "Count"]

fig_pie = px.pie(
    mood_counts,
    names="Mood",
    values="Count",
    color_discrete_sequence=["#7C3AED", "#059669", "#F59E0B"]
)
fig_pie.update_layout(
    paper_bgcolor="rgba(0,0,0,0)"
)
st.plotly_chart(fig_pie, use_container_width=True)

# ── Most common words ────────────────────────────────────────────
st.subheader("What You Write About Most")
st.caption("Most frequently used words across all your entries.")

# Combine all entries into one string
all_text = " ".join(df["entry"].tolist()).lower()

# Remove common filler words (stopwords) so we see meaningful words
stopwords = set([
    "i", "me", "my", "the", "a", "an", "and", "or", "but", "in",
    "on", "at", "to", "for", "of", "with", "is", "it", "this",
    "that", "was", "are", "be", "have", "has", "had", "do", "did",
    "so", "just", "not", "about", "up", "out", "from", "as", "also",
    "been", "would", "could", "should", "will", "can", "more", "very",
    "when", "what", "how", "all", "now", "like", "some", "they",
    "their", "there", "we", "you", "your", "he", "she", "am", "im",
    "its", "if", "no", "any", "get", "got", "one", "still", "want",
    "know", "think", "feel", "things", "time", "dont", "really"
])

words = re.findall(r'\b[a-z]{4,}\b', all_text)
filtered = [w for w in words if w not in stopwords]
word_freq = Counter(filtered).most_common(20)

if word_freq:
    words_df = pd.DataFrame(word_freq, columns=["Word", "Count"])
    fig_bar = px.bar(
        words_df,
        x="Count",
        y="Word",
        orientation="h",
        color="Count",
        color_continuous_scale="Purples"
    )
    fig_bar.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(autorange="reversed"),
        showlegend=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Recent reflections ───────────────────────────────────────────
st.markdown("---")
st.subheader("Recent AI Reflections")

for _, row in df.tail(3).iterrows():
    with st.expander(f"📅 {row['date'].strftime('%d %B %Y')} — {row['mood_label']}"):
        st.write(row["ai_reflection"])