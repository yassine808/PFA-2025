# MarHist — Chatbot IA sur l'Histoire du Maroc

MarHist is a French-language AI chatbot web application that lets users explore the history of Morocco through an interactive conversational interface. It uses a Retrieval-Augmented Generation (RAG) pipeline powered by LangChain and a local Ollama LLM, with a Flask backend and a clean Bootstrap-based frontend.

## Features

- **AI Chatbot** — Ask questions about Moroccan history and get answers sourced from curated historical documents
- **User Accounts** — Sign up, log in, and manage your profile (name, username, gender, password)
- **Chat History** — Conversations are saved per user and persist across sessions
- **Streaming Responses** — Answers stream token-by-token for a smooth chat experience
- **RAG Pipeline** — Responses are grounded in real historical data, not just the model's training knowledge

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask |
| **Frontend** | HTML, CSS, JavaScript (Bootstrap) |
| **AI / LLM** | Ollama (Llama 3), LangChain |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` |
| **Vector Store** | ChromaDB |
| **Data** | Excel files (scraped historical content) |
| **Session** | Flask-Session (filesystem) |

## Project Structure

```
├── Flask/
│   ├── run.py                     # Entry point — starts the Flask dev server
│   ├── requirements.txt           # Python dependencies
│   ├── users.txt                  # User accounts (JSON lines)
│   ├── user_data/                 # Per-user chat history (JSON)
│   ├── chroma_db/                 # ChromaDB persisted vector store
│   ├── flask_session/             # Flask session files
│   ├── Scraped*.xlsx              # Historical data sources
│   ├── static/                    # Profile pictures and shared assets
│   └── app/
│       ├── __init__.py            # App factory
│       ├── routes.py              # All route handlers and user management
│       ├── DLchatbotFrancais.py   # RAG pipeline (data loading, embeddings, LLM)
│       ├── templates/             # HTML templates
│       └── static/                # CSS, images, video assets
├── pfa.pptx                       # Project presentation
└── README.md                      # This file
```

## Prerequisites

- **Python 3.10+**
- **Ollama** installed and running locally with the `llama3` model pulled:
  ```bash
  ollama pull llama3
  ```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yassine808/PFA-2025.git
   cd PFA-2025
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   venv\Scripts\activate    # Windows
   pip install -r Flask/requirements.txt
   ```

3. **Start Ollama** (in a separate terminal):
   ```bash
   ollama serve
   ```
   Make sure the `llama3` model is available:
   ```bash
   ollama list
   ```

4. **Run the application:**
   ```bash
   cd Flask
   python run.py
   ```

5. **Open your browser** and go to `http://localhost:5000`

## Usage

1. **Sign up** for a new account at `/signup`
2. **Log in** at `/login`
3. Navigate to the **Chatbot** page to start asking questions about Moroccan history
4. Visit your **Profile** page to update your info or change your password
5. Your chat history is automatically saved and restored on each login

## Data Sources

The chatbot's knowledge comes from four Excel files scraped from historical sources:

| File | Theme |
|---|---|
| `ScrapedPeriodeColoniale.xlsx` | Période Coloniale |
| `ScrapedINDEPENDENCE.xlsx` | Indépendance |
| `ScrapedReformesRecentes.xlsx` | Réformes Récentes |
| `ScrapedREGNEDEHASSANII.xlsx` | Règne de Hassan II |

Each file contains rows with `content`, `subtheme`, and `status` columns. Only rows marked as `scraped` are loaded into the vector store during the first startup.

## How the RAG Pipeline Works

1. **Data Loading** — Excel files are read with pandas and converted to LangChain `Document` objects
2. **Chunking** — Documents are split into chunks (1M chars with 200-char overlap)
3. **Embedding** — Each chunk is embedded using HuggingFace's `all-MiniLM-L6-v2`
4. **Storage** — Embeddings are persisted in ChromaDB (`./chroma_db`)
5. **Retrieval** — At query time, the top-4 most relevant chunks are retrieved
6. **Generation** — The chunks are injected into a prompt template alongside the user's question, and the Ollama LLM (Llama 3) generates a streaming response

## Notes

- Ollama must be running at `http://localhost:11434` for the chatbot to work
- The first run builds the vector store, which may take a few seconds
- User passwords are stored in plaintext (this is a student project — not production-grade security)
- Chat history is stored as JSON files in `Flask/user_data/` and also kept in the Flask session
