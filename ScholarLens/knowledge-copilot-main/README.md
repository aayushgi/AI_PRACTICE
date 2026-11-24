<p align="center">
  <h1 align="center">🧠 Knowledge Copilot</h1>
  <p align="center">
    A RAG-powered AI chatbot that answers questions grounded in your research papers — with persistent memory, streaming responses, and a modern React UI.
  </p>
</p>

<br/>

## ✨ Features

| Feature | Description |
|---|---|
| **RAG Pipeline** | Retrieval-Augmented Generation using BGE-M3 embeddings + PostgreSQL pgvector for semantic search over research papers |
| **Streaming Chat** | Real-time token-by-token response streaming via Server-Sent Events (SSE) |
| **User Memory** | Automatically extracts and remembers user preferences/interests across sessions using Redis |
| **Chat Sessions** | Create, rename, and delete independent chat sessions with full message history |
| **PDF Preprocessing** | Industry-grade PDF text extraction with OCR fix, hyphen repair, academic noise removal, and unicode normalization |
| **Smart Chunking** | Sentence-aware text chunking with token-level overlap for optimal retrieval quality |
| **Markdown Rendering** | Full markdown + GFM support in chat responses (tables, code blocks, lists) |
| **Model Switching** | Dynamically switch between any locally available Ollama model |
| **Infinite Scroll** | Cursor-based paginated message loading for efficient chat history browsing |

<br/>

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React 19)                   │
│        Vite · Tailwind CSS v4 · react-markdown          │
└────────────────────────┬────────────────────────────────┘
                         │  HTTP / SSE
┌────────────────────────▼────────────────────────────────┐
│                  Backend (FastAPI)                       │
│         uvicorn · httpx · pydantic · async I/O          │
├─────────────┬──────────────┬────────────────────────────┤
│  Ollama     │  PostgreSQL  │  Redis                     │
│  (LLM)     │  (Chat + RAG)│  (User Memory)             │
└─────────────┴──────────────┴────────────────────────────┘
```

<br/>

## 📂 Project Structure

```
ChatBot/
├── backend/
│   ├── main.py                 # FastAPI server & API routes
│   ├── ollama_service.py       # LLM interaction, system prompts, memory updates
│   ├── db.py                   # Chat message & session persistence (PostgreSQL)
│   ├── db_rag.py               # RAG vector store — embedding + semantic search
│   ├── preprocessing_rag.py    # PDF text extraction & cleaning pipeline
│   ├── populate_db.py          # Chunking & database population script
│   ├── redis_client.py         # Redis client for user memory storage
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables (not committed)
│   └── data/                   # Research paper PDFs (knowledge base)
│
└── frontend/
    ├── src/
    │   ├── App.jsx             # Root component with health check & model init
    │   ├── components/
    │   │   ├── ChatContainer.jsx    # Main chat orchestrator
    │   │   ├── ChatInput.jsx        # Message input with send/stop controls
    │   │   ├── MessageBubble.jsx    # Individual message renderer (markdown)
    │   │   ├── MessageList.jsx      # Scrollable message list with pagination
    │   │   ├── ModelSelector.jsx    # Ollama model dropdown
    │   │   ├── Sidebar.jsx          # Chat session management panel
    │   │   └── TypingIndicator.jsx  # Animated typing dots
    │   └── services/
    │       └── api.js           # API client (fetch + SSE streaming)
    ├── package.json
    └── vite.config.js
```

<br/>

## ⚙️ Prerequisites

| Dependency | Purpose |
|---|---|
| **Python 3.10+** | Backend runtime |
| **Node.js 18+** | Frontend tooling |
| **PostgreSQL 15+** | Chat history + vector store (with `pgvector` extension) |
| **Redis** | User memory cache |
| **Ollama** | Local LLM inference engine |
| **CUDA GPU** *(recommended)* | Accelerates BGE-M3 embedding model |

<br/>

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/gurusewak-singh/knowledge-copilot.git
cd knowledge-copilot
```

### 2. Set Up PostgreSQL

Create two databases and enable the `pgvector` extension:

```sql
-- Chat database
CREATE DATABASE chatdb;
\c chatdb

CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    chat_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    chat_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) DEFAULT 'New Chat',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RAG database
CREATE DATABASE ragdb;
\c ragdb
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
    id VARCHAR(100) PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1024)
);
```

### 3. Set Up Redis

```bash
# Linux / macOS
sudo systemctl start redis

# Windows (via WSL or Docker)
docker run -d --name redis -p 6379:6379 redis
```

### 4. Set Up Ollama

```bash
# Install from https://ollama.com
# Pull a model
ollama pull llama3
```

### 5. Configure Environment Variables

Create `backend/.env`:

```env
# Chat DB
CHAT_DB_NAME=chatdb
CHAT_DB_USER=postgres
CHAT_DB_PASSWORD=your_password
CHAT_DB_HOST=localhost
CHAT_DB_PORT=5432

# RAG DB
RAG_DB_NAME=ragdb
RAG_DB_USER=postgres
RAG_DB_PASSWORD=your_password
RAG_DB_HOST=localhost
RAG_DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
```

### 6. Install & Run the Backend

```bash
cd backend
pip install -r requirements.txt

# Populate the vector database with your PDFs (one-time)
python populate_db.py

# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Install & Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

<br/>

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check (API + Ollama status) |
| `GET` | `/api/models` | List available Ollama models |
| `POST` | `/api/chat` | Stream a chat response (SSE) |
| `POST` | `/api/stop` | Save partial response on stop |
| `POST` | `/api/chat/new` | Create a new chat session |
| `POST` | `/api/chat/delete` | Delete a chat session |
| `POST` | `/api/chat/rename` | Rename a chat session |
| `GET` | `/api/chat/sessions` | List all chat sessions |
| `GET` | `/api/messages` | Paginated message retrieval |

<br/>

## 🧩 Tech Stack

**Backend:** Python · FastAPI · Uvicorn · httpx · psycopg2 · Redis · PyTorch · FlagEmbedding (BGE-M3) · Transformers · PyMuPDF

**Frontend:** React 19 · Vite · Tailwind CSS v4 · react-markdown · remark-gfm

**Infrastructure:** PostgreSQL (pgvector) · Redis · Ollama

<br/>

## 📄 Knowledge Base

The RAG pipeline is pre-loaded with research papers on core AI/ML topics:

- *Attention Is All You Need* — Transformer architecture
- *Build a Large Language Model (From Scratch)* — LLM fundamentals
- *HybridRAG: Integrating Knowledge Graphs and Vector Retrieval*
- *Modular RAG* — Modular retrieval-augmented generation framework
- *RAG Research Paper* — Retrieval-augmented generation foundations
- *VL-JEPA Research Paper* — Vision-language joint embedding

> Drop your own PDFs into `backend/data/`, update the file list in `preprocessing_rag.py`, and run `python populate_db.py` to index them.

<br/>

## 📝 License

This project is open source. Feel free to use and modify it for your own purposes.
