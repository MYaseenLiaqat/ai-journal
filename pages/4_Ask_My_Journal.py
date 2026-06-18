import streamlit as st
import sqlite3
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from datetime import datetime

load_dotenv()

st.set_page_config(page_title="Ask My Journal", page_icon="🔍", layout="wide")
st.title("🔍 Ask My Journal")
st.markdown("Ask anything about your past entries. The AI searches your writing by meaning, not just keywords.")
st.markdown("---")

# ── Load entries from database ───────────────────────────────────
def load_entries():
    conn = sqlite3.connect("data/journal.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, entry, mood_label, ai_reflection FROM entries ORDER BY created_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# ── Build ChromaDB vector store from entries ─────────────────────
# This is the core of RAG
# We take each journal entry, convert it to a vector using a 
# sentence transformer model, and store it in ChromaDB
# Later when you ask a question, your question also becomes a vector
# and ChromaDB finds the closest matching entries
@st.cache_resource
def build_vector_store():
    entries = load_entries()

    if not entries:
        return None

    # Convert each entry into a LangChain Document object
    # Documents have content (the text) and metadata (date, mood etc)
    documents = []
    for row in entries:
        doc = Document(
            page_content=row[2],  # the actual journal entry text
            metadata={
                "id": row[0],
                "date": row[1],
                "mood": row[3],
                "reflection": row[4]
            }
        )
        documents.append(doc)

    # Load the embedding model — this runs locally, no API needed
    # It converts text into 384-dimensional vectors
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Store documents + their vectors in ChromaDB
    # persist_directory saves them to disk so we don't rebuild every time
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="data/chroma_db"
    )

    return vector_store

# ── Answer question using RAG ────────────────────────────────────
def ask_journal(question, vector_store):
    # Step 1: find the 3 most relevant entries for this question
    relevant_docs = vector_store.similarity_search(question, k=3)

    if not relevant_docs:
        return "No relevant entries found.", []

    # Step 2: build context from those entries
    context = ""
    for i, doc in enumerate(relevant_docs):
        context += f"\nEntry {i+1} ({doc.metadata['date']}, mood: {doc.metadata['mood']}):\n"
        context += doc.page_content + "\n"

    # Step 3: send context + question to LLaMA 3
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",
        temperature=0.5
    )

    system_prompt = """You are helping Yaseen understand patterns in his own journal.
You have been given relevant journal entries that match his question.

Answer his question based ONLY on what's in his journal entries.
- Be specific — reference dates and actual things he wrote
- If the entries don't fully answer the question, say so honestly
- Keep your answer under 150 words
- Speak directly to him using "you"
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"My question: {question}\n\nRelevant journal entries:\n{context}")
    ]

    response = llm.invoke(messages)
    return response.content, relevant_docs

# ── UI ───────────────────────────────────────────────────────────
entries = load_entries()

if not entries:
    st.info("No journal entries yet. Write a few entries first then come back here.")
    st.stop()

st.markdown(f"**{len(entries)} entries** in your journal available to search.")

# Build vector store
with st.spinner("Loading your journal into memory..."):
    vector_store = build_vector_store()

if vector_store is None:
    st.error("Could not build search index. Write some entries first.")
    st.stop()

st.success("Journal loaded and ready ✅")
st.markdown("---")

# Question input
st.subheader("Ask a question")

# Example questions to get started
st.caption("Try asking:")
example_cols = st.columns(3)
examples = [
    "When was I most stressed?",
    "What have I said about my job search?",
    "What are my biggest worries?"
]
for i, example in enumerate(examples):
    with example_cols[i]:
        if st.button(example, key=f"ex_{i}"):
            st.session_state["question"] = example

question = st.text_input(
    "Your question",
    value=st.session_state.get("question", ""),
    placeholder="What have I been worrying about most?",
    label_visibility="collapsed"
)

if st.button("🔍 Search my journal", type="primary") and question:
    with st.spinner("Searching your entries..."):
        answer, relevant_docs = ask_journal(question, vector_store)

    st.markdown("### Answer")
    st.info(answer)

    # Show which entries were used to answer
    if relevant_docs:
        st.markdown("### Entries used to answer this")
        for doc in relevant_docs:
            with st.expander(f"📅 {doc.metadata['date']} — {doc.metadata['mood']}"):
                st.write(doc.page_content)

# Clear cached vector store button
# This is needed when you add new entries — the cache needs rebuilding
st.markdown("---")
st.caption("Added new entries and results seem outdated?")
if st.button("🔄 Rebuild search index"):
    st.cache_resource.clear()
    st.rerun()