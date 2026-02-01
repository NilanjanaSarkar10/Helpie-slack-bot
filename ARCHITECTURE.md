# Project Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Slack Workspace                       │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐  │
│  │  Channels  │  │    DMs     │  │  Slash Commands      │  │
│  │  @BotName  │  │  Messages  │  │  /bot-help, etc.     │  │
│  └──────┬─────┘  └──────┬─────┘  └──────────┬───────────┘  │
└─────────┼────────────────┼───────────────────┼──────────────┘
          │                │                   │
          └────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Socket Mode │
                    │  Connection  │
                    └──────┬───────┘
                           │
        ┌──────────────────▼──────────────────┐
        │       slack_bot.py (Main App)       │
        │  - Event Listeners                   │
        │  - Command Handlers                  │
        │  - Message Routing                   │
        └──────┬───────────────────┬───────────┘
               │                   │
      ┌────────▼────────┐   ┌─────▼──────────┐
      │  llama_ai.py    │   │ knowledge_base │
      │  - AI Queries   │   │   _manager.py  │
      │  - History      │   │  - Doc Loading │
      │  - Prompts      │   │  - Embedding   │
      └────────┬────────┘   │  - Search      │
               │            └─────┬──────────┘
               │                  │
        ┌──────▼────────┐   ┌────▼──────────┐
        │    Ollama     │   │   ChromaDB    │
        │ ┌───────────┐ │   │  Vector Store │
        │ │  Llama    │ │   │               │
        │ │  Model    │ │   │  Embeddings   │
        │ └───────────┘ │   │               │
        └───────────────┘   └───────────────┘
```

## Data Flow

### User Query Processing

```
User sends message
       │
       ▼
Slack receives message
       │
       ▼
Socket Mode forwards to bot
       │
       ▼
slack_bot.py receives event
       │
       ├─► Extract user message
       │
       ▼
Search Knowledge Base
       │
       ├─► Embed query using sentence-transformers
       ├─► Search ChromaDB for similar content
       └─► Return top 3 relevant chunks
       │
       ▼
Build Context Prompt
       │
       ├─► Combine retrieved documents
       ├─► Add conversation history
       └─► Format prompt for Llama
       │
       ▼
Generate Response with Llama
       │
       ├─► Send to Ollama API
       ├─► Llama processes with context
       └─► Return AI response
       │
       ▼
Format and Send to Slack
       │
       ├─► Add source citations
       ├─► Format message
       └─► Send via Slack API
```

## Component Details

### 1. slack_bot.py
**Purpose:** Main application entry point
**Functions:**
- Listen for Slack events (mentions, DMs)
- Handle slash commands
- Coordinate between AI and knowledge base
- Format responses

### 2. llama_ai.py
**Purpose:** AI response generation
**Functions:**
- Communicate with Ollama
- Manage conversation history
- Build prompts with context
- Handle model interactions

### 3. knowledge_base_manager.py
**Purpose:** Document storage and retrieval
**Functions:**
- Load documents (PDF, DOCX, TXT)
- Chunk text for embedding
- Store in ChromaDB
- Semantic search
- Return relevant context

### 4. ChromaDB
**Purpose:** Vector database
**Storage:**
- Document embeddings
- Metadata (source, type)
- Efficient similarity search

### 5. Ollama
**Purpose:** Run Llama models locally
**Features:**
- No external API calls
- Privacy-focused
- Free to use
- Multiple model options

## File Structure

```
slack-ai-bot/
│
├── Core Application Files
│   ├── slack_bot.py              # Main bot application
│   ├── llama_ai.py               # AI handler
│   ├── knowledge_base_manager.py # Search engine
│   └── requirements.txt          # Dependencies
│
├── Configuration
│   ├── .env                      # Your secrets (create this)
│   ├── .env.example             # Template
│   └── .gitignore               # Git ignore rules
│
├── Setup Scripts
│   ├── setup.sh                 # Linux/Mac setup
│   ├── setup.bat                # Windows setup
│   └── test_setup.py            # Verify installation
│
├── Documentation
│   ├── README.md                # Complete guide
│   ├── QUICKSTART.md            # 5-minute setup
│   └── sample_faq.txt           # Example knowledge base
│
└── Data (created at runtime)
    ├── knowledge_base/          # Your documents
    │   ├── chroma_db/          # Vector database
    │   ├── document1.pdf
    │   └── faq.txt
    └── venv/                    # Python virtual environment
```

## Technology Stack

### Backend
- **Python 3.8+**: Core language
- **Slack Bolt**: Slack integration framework
- **Socket Mode**: Real-time Slack connection

### AI Components
- **Ollama**: Run Llama models locally
- **Llama 3.2**: Language model (3B parameters)
- **Sentence Transformers**: Text embeddings

### Data Storage
- **ChromaDB**: Vector database
- **PyPDF2**: PDF processing
- **python-docx**: Word document processing

## Key Features Explained

### 1. Socket Mode
- No public URL needed
- Works behind firewalls
- Real-time bidirectional communication
- Easier development setup

### 2. Semantic Search
- Converts text to vector embeddings
- Finds similar content (not just keywords)
- Returns relevant context for AI
- Efficient with large knowledge bases

### 3. Conversation Memory
- Stores last 5 exchanges per user
- Provides context to AI
- Makes conversations natural
- Automatically managed

### 4. Context-Aware Responses
- Searches knowledge base first
- Provides sources to AI
- AI can cite specific documents
- Falls back to general knowledge

## Message Flow Example

```
User: "@BotName what's the refund policy?"
  │
  ▼
Knowledge Base Search:
  - "refund policy" → embedding
  - ChromaDB finds: "30-day money-back guarantee..."
  │
  ▼
Build Prompt:
  "Here is relevant info: [Source: FAQ] 30-day money-back...
   Question: what's the refund policy?"
  │
  ▼
Llama Generates:
  "We offer a 30-day money-back guarantee. If you're not
   satisfied, contact support for a full refund within 30 days."
  │
  ▼
Format Response:
  "@User We offer a 30-day money-back guarantee...
   📚 Sources: FAQ"
  │
  ▼
Send to Slack ✓
```

## Security Considerations

### Data Privacy
- All processing happens locally
- No data sent to external AI APIs
- Knowledge base stored on your machine
- Slack tokens kept in .env (not in code)

### Access Control
- Bot only responds to authorized workspace
- Conversation history per user
- Slack handles authentication
- Can restrict to specific channels

## Scaling Considerations

### Current Setup (Good for):
- Small to medium teams (< 100 users)
- 1,000-10,000 messages/day
- Knowledge base < 10,000 documents
- Single server deployment

### To Scale Up:
- Use PostgreSQL for conversation history
- Deploy ChromaDB separately
- Load balance multiple bot instances
- Use GPUs for faster Llama inference
- Consider cloud-hosted Ollama

## Performance Tips

1. **Model Selection:**
   - llama3.2:1b - Fastest, basic quality
   - llama3.2:3b - Balanced (recommended)
   - llama3.1:8b - Best quality, slower

2. **Knowledge Base:**
   - Keep documents focused and relevant
   - Remove outdated content
   - Use clear, concise language
   - Organize by topic

3. **Search Results:**
   - Adjust n_results (default: 3)
   - Balance speed vs context
   - Monitor ChromaDB performance

4. **Conversation History:**
   - Current: Last 5 exchanges
   - Adjust based on needs
   - Clear when changing topics

## Troubleshooting Guide

### Bot Not Responding
1. Check Ollama: `ollama list`
2. Check bot logs in terminal
3. Verify Slack tokens in .env
4. Test with: `python test_setup.py`

### Slow Responses
1. Try smaller model: `llama3.2:1b`
2. Reduce search results: `n_results=2`
3. Clear conversation history
4. Check system resources

### Inaccurate Answers
1. Add more knowledge base content
2. Update outdated documents
3. Increase search results: `n_results=5`
4. Try larger model: `llama3.1:8b`

### Import Errors
```bash
pip install -r requirements.txt --upgrade
```

### ChromaDB Issues
Delete and rebuild:
```bash
rm -rf knowledge_base/chroma_db
python slack_bot.py  # Rebuilds automatically
```
