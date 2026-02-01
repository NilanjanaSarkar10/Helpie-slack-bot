# Slack AI Bot with Llama & Custom Knowledge Base

A fully-featured Slack bot powered by Llama AI (via Ollama) with a custom knowledge base using ChromaDB for semantic search.

## 🌟 Features

- **AI-Powered Responses**: Uses Llama AI through Ollama for intelligent responses
- **Custom Knowledge Base**: Load PDFs, DOCX, and TXT files for context-aware answers
- **Semantic Search**: ChromaDB with sentence transformers for finding relevant information
- **Conversation History**: Remembers context from recent messages
- **Channel & DM Support**: Works in channels (when mentioned) and direct messages
- **Source Citations**: Shows which documents were used to answer questions
- **Slash Commands**: Built-in commands for help, stats, and clearing history

## 📋 Prerequisites

1. **Python 3.8+**
2. **Ollama** - For running Llama models locally
3. **Slack Workspace** - Admin access to create apps

## 🚀 Installation Guide

### Step 1: Install Ollama

**For Windows:**
1. Download from: https://ollama.ai/download/windows
2. Run the installer
3. Open Command Prompt and verify: `ollama --version`

**For Mac:**
```bash
brew install ollama
```

**For Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: Download Llama Model

```bash
ollama pull llama3.2:3b
```

Alternative models (choose based on your hardware):
- `llama3.2:1b` - Smallest, fastest (1GB)
- `llama3.2:3b` - Recommended (2GB) ✅
- `llama3.1:8b` - Better quality (4.7GB)

Start Ollama service:
```bash
ollama serve
```

### Step 3: Clone/Create Project

Create a new folder for your project:
```bash
mkdir slack-ai-bot
cd slack-ai-bot
```

Copy all the Python files into this folder:
- `slack_bot.py`
- `knowledge_base_manager.py`
- `llama_ai.py`
- `requirements.txt`
- `.env.example`

### Step 4: Set Up Python Environment

**Create virtual environment:**
```bash
python -m venv venv
```

**Activate it:**
- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

**Install dependencies:**
```bash
pip install -r requirements.txt
```

### Step 5: Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name it (e.g., "AI Assistant") and select your workspace

**Configure OAuth & Permissions:**
1. Go to **"OAuth & Permissions"**
2. Add these **Bot Token Scopes**:
   - `app_mentions:read`
   - `chat:write`
   - `im:history`
   - `im:read`
   - `im:write`
   - `channels:history`
   - `groups:history`
   - `mpim:history`
3. Click **"Install to Workspace"** → **"Allow"**
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)

**Enable Socket Mode:**
1. Go to **"Socket Mode"** in sidebar
2. Enable Socket Mode
3. Create an **App-Level Token**:
   - Name: `socket_token`
   - Scope: `connections:write`
   - Copy the token (starts with `xapp-`)

**Enable Events:**
1. Go to **"Event Subscriptions"**
2. Enable Events
3. Under **Subscribe to bot events**, add:
   - `app_mention`
   - `message.im`

**Enable Home Tab:**
1. Go to **"App Home"**
2. Enable **Home Tab**
3. Check **"Allow users to send Slash commands and messages from the messages tab"**

**Add Slash Commands:**
1. Go to **"Slash Commands"**
2. Create these commands:
   - Command: `/bot-help`, Description: "Show bot help"
   - Command: `/bot-stats`, Description: "Show knowledge base stats"
   - Command: `/bot-clear`, Description: "Clear conversation history"

### Step 6: Configure Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and fill in your values:
```env
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434
KNOWLEDGE_BASE_PATH=./knowledge_base
```

Get your **Signing Secret**:
1. Go to **"Basic Information"** in Slack app settings
2. Under **App Credentials**, copy the **Signing Secret**

### Step 7: Add Knowledge Base Documents

Create a `knowledge_base` folder:
```bash
mkdir knowledge_base
```

Add your documents (PDFs, DOCX, or TXT files) to this folder. The bot will automatically load them on startup.

Example files you can add:
- Company policies
- Product documentation
- FAQs
- Training materials
- Any text-based information

### Step 8: Run the Bot

Make sure Ollama is running:
```bash
ollama serve
```

In a new terminal, start the bot:
```bash
python slack_bot.py
```

You should see:
```
INFO - Starting Slack bot in Socket Mode...
INFO - Knowledge Base: X documents loaded
⚡️ Bolt app is running!
```

## 💬 Using the Bot

### In Channels:
```
@BotName What is our refund policy?
```

### In Direct Messages:
Just type your question directly:
```
How do I reset my password?
```

### Slash Commands:
- `/bot-help` - Show help
- `/bot-stats` - View statistics
- `/bot-clear` - Clear your conversation history

## 📁 Project Structure

```
slack-ai-bot/
├── slack_bot.py              # Main bot application
├── knowledge_base_manager.py # Document processing & search
├── llama_ai.py               # Llama AI integration
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── .env.example             # Environment template
├── knowledge_base/          # Your documents folder
│   ├── document1.pdf
│   ├── document2.docx
│   └── faq.txt
└── README.md
```

## 🔧 Configuration Options

### Change AI Model

Edit `.env`:
```env
OLLAMA_MODEL=llama3.1:8b
```

Then download it:
```bash
ollama pull llama3.1:8b
```

### Adjust Search Results

In `slack_bot.py`, modify `n_results`:
```python
context = kb.search(text, n_results=5)  # Get top 5 results instead of 3
```

### Change Chunk Size

In `knowledge_base_manager.py`, modify `_chunk_text`:
```python
def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100):
```

## 🐛 Troubleshooting

### Bot doesn't respond:
1. Check Ollama is running: `ollama list`
2. Verify bot is running: check terminal for errors
3. Check Slack permissions are correct
4. Verify `.env` tokens are correct

### "Model not found" error:
```bash
ollama pull llama3.2:3b
```

### Knowledge base is empty:
- Check `knowledge_base/` folder exists
- Add .pdf, .docx, or .txt files
- Restart the bot

### Import errors:
```bash
pip install -r requirements.txt --upgrade
```

### Connection refused to Ollama:
Make sure Ollama is running:
```bash
ollama serve
```

## 🔒 Security Notes

- Keep your `.env` file private (never commit to Git)
- Tokens grant access to your Slack workspace
- Knowledge base documents are stored locally
- Ollama runs locally (no external API calls for AI)

## 📝 Adding to Git

Create `.gitignore`:
```
.env
venv/
__pycache__/
*.pyc
knowledge_base/chroma_db/
.DS_Store
```

## 🎯 Next Steps

1. Add more documents to knowledge base
2. Customize responses in `llama_ai.py`
3. Add custom slash commands
4. Integrate with other tools
5. Add analytics/logging

## 📚 Resources

- [Slack API Documentation](https://api.slack.com/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Slack Bolt Python](https://slack.dev/bolt-python/)

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review Slack app configuration
3. Verify Ollama is working: `ollama run llama3.2:3b "Hello"`
4. Check bot logs in terminal

## 📄 License

MIT License - Feel free to modify and use for your projects!
