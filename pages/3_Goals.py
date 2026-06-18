import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os

load_dotenv()

st.set_page_config(page_title="Goals", page_icon="🎯", layout="wide")
st.title("🎯 Goals Tracker")
st.markdown("Set goals, track progress, get held accountable.")
st.markdown("---")

# ── Database setup ───────────────────────────────────────────────
def init_goals_db():
    conn = sqlite3.connect("data/journal.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT,
            category TEXT,
            deadline TEXT,
            status TEXT DEFAULT 'active',
            progress INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_goals_db()

def load_goals():
    conn = sqlite3.connect("data/journal.db")
    df = pd.read_sql_query(
        "SELECT * FROM goals ORDER BY deadline ASC", conn
    )
    conn.close()
    return df

def save_goal(goal, category, deadline, notes):
    conn = sqlite3.connect("data/journal.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO goals (goal, category, deadline, notes, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (goal, category, str(deadline), notes,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def update_progress(goal_id, progress, status):
    conn = sqlite3.connect("data/journal.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE goals SET progress = ?, status = ? WHERE id = ?
    """, (progress, status, goal_id))
    conn.commit()
    conn.close()

def delete_goal(goal_id):
    conn = sqlite3.connect("data/journal.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()

# ── AI accountability coach ──────────────────────────────────────
def get_goal_advice(goals_summary):
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",
        temperature=0.7
    )

    system_prompt = """You are Yaseen's personal accountability coach. 
He is a CS graduate from Lahore, Pakistan, actively job hunting for 
ML/Data Science roles, wants to move abroad for Masters on scholarship, 
and is building his skills.

Look at his current goals and:
1. Identify which goal needs the most urgent attention right now
2. Give one specific action he can take TODAY for his most important goal
3. Call out any goal that seems vague or needs a clearer deadline
4. Give one honest, direct observation about his goal-setting patterns

Keep it under 120 words. Be direct, not motivational-poster-ish."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Here are my current goals:\n\n{goals_summary}")
    ]

    response = llm.invoke(messages)
    return response.content

# ── Add new goal ─────────────────────────────────────────────────
st.subheader("Add a New Goal")

with st.form("goal_form"):
    col1, col2 = st.columns(2)
    with col1:
        goal_text = st.text_input(
            "What's the goal?",
            placeholder="e.g. Get a Data Science job at an international company"
        )
        category = st.selectbox(
            "Category",
            ["Career", "Skills", "Education", "Health", "Finance", "Personal"]
        )
    with col2:
        deadline = st.date_input(
            "Deadline",
            min_value=date.today()
        )
        notes = st.text_area(
            "Why does this matter to you?",
            placeholder="Be specific — vague goals don't get done",
            height=100
        )

    submitted = st.form_submit_button("➕ Add Goal", type="primary")
    if submitted:
        if goal_text.strip():
            save_goal(goal_text, category, deadline, notes)
            st.success("Goal added ✅")
            st.rerun()
        else:
            st.warning("Write the goal first.")

# ── Current goals ────────────────────────────────────────────────
st.markdown("---")
df = load_goals()

if df.empty:
    st.info("No goals yet. Add your first one above ☝️")
else:
    # Summary metrics
    active = df[df["status"] == "active"]
    completed = df[df["status"] == "completed"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Active Goals", len(active))
    with col2:
        st.metric("Completed", len(completed))
    with col3:
        if not active.empty:
            avg_progress = int(active["progress"].mean())
            st.metric("Avg Progress", f"{avg_progress}%")

    st.markdown("---")

    # Group by category
    categories = df["category"].unique()

    for cat in categories:
        cat_goals = df[df["category"] == cat]
        st.subheader(f"{cat} ({len(cat_goals)})")

        for _, row in cat_goals.iterrows():
            # Color code by status
            if row["status"] == "completed":
                border = "2px solid #059669"
            elif row["deadline"] < str(date.today()):
                border = "2px solid #DC2626"  # overdue = red
            else:
                border = "0.5px solid var(--color-border-tertiary)"

            with st.expander(
                f"{'✅' if row['status'] == 'completed' else '🎯'} {row['goal']} — due {row['deadline']}"
            ):
                if row["notes"]:
                    st.caption(f"Why it matters: {row['notes']}")

                # Progress slider
                new_progress = st.slider(
                    "Progress",
                    0, 100,
                    int(row["progress"]),
                    key=f"progress_{row['id']}"
                )

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    new_status = st.selectbox(
                        "Status",
                        ["active", "completed", "paused"],
                        index=["active", "completed", "paused"].index(row["status"]),
                        key=f"status_{row['id']}"
                    )
                with col_b:
                    if st.button("💾 Update", key=f"update_{row['id']}"):
                        update_progress(row["id"], new_progress, new_status)
                        st.rerun()
                with col_c:
                    if st.button("🗑️ Delete", key=f"delete_{row['id']}"):
                        delete_goal(row["id"])
                        st.rerun()

    # ── AI coach section ─────────────────────────────────────────
    st.markdown("---")
    st.subheader("🤖 AI Accountability Coach")
    st.caption("Get honest feedback on your current goals.")

    if st.button("Get coached", type="primary"):
        goals_summary = "\n".join([
            f"- [{row['category']}] {row['goal']} | deadline: {row['deadline']} | progress: {row['progress']}% | status: {row['status']}"
            for _, row in df.iterrows()
        ])
        with st.spinner("Reading your goals..."):
            advice = get_goal_advice(goals_summary)
        st.info(advice)