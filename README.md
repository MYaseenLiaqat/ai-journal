# AI Growth Journal 📓

A personal AI-powered journal that learns about you over time — your goals, 
patterns, strengths and weaknesses — and becomes a genuine thinking partner.

## Features
- **Daily Journal** — write entries, get AI reflections from LLaMA 3
- **Insights Dashboard** — mood and energy trends over time
- **Goals Tracker** — set goals, track progress, get AI coaching
- **Ask My Journal** — semantic search over all your entries using RAG

## Tech Stack
- **LLM:** Groq API (LLaMA 3.3 70B) via LangChain
- **Vector Database:** ChromaDB with sentence-transformers embeddings
- **Sentiment Analysis:** TextBlob
- **Frontend:** Streamlit
- **Visualization:** Plotly
- **Storage:** SQLite

## Setup

1. Clone the repo
```bash
   git clone https://github.com/MYaseenLiaqat/ai-journal.git
   cd ai-journal
```

2. Create virtual environment
```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Mac/Linux
```

3. Install dependencies
```bash
   pip install -r requirements.txt
```

4. Add your Groq API key
```bash
   # Create a .env file and add:
   GROQ_API_KEY=your_key_here
```

5. Run the app
```bash
   streamlit run app.py
```

## Get a free Groq API key
Sign up at [console.groq.com](https://console.groq.com)
