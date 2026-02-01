# 🚀 QUICK START GUIDE

## 5-Minute Setup

### Step 1: Install Ollama (2 minutes)

**Windows:**
```
Download from: https://ollama.ai/download/windows
Run installer
```

**Mac:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: Download AI Model (2 minutes)

Open terminal and run:
```bash
ollama serve
```

In a new terminal:
```bash
ollama pull llama3.2:3b
```

### Step 3: Install Python Dependencies (1 minute)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Create Slack App (5 minutes)

1. Go to: https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name: "AI Assistant", select your workspace

**Add Permissions:**
- Go to **OAuth & Permissions**
- Add Bot Token Scopes:
  - `app_mentions:read`
  - `chat:write`
  - `im:history`
  - `im:read`
  - `im:write`
  - `channels:history`
- Click **"Install to Workspace"**
- Copy **Bot User OAuth Token** (xoxb-...)

**Enable Socket Mode:**
- Go to **Socket Mode**
- Enable it
- Create token with scope `connections:write`
- Copy **App Token** (xapp-...)

**Enable Events:**
- Go to **Event Subscriptions**
- Toggle On
- Add Bot Events: `app_mention`, `message.im`

**Enable Home Tab:**
- Go to **App Home**
- Enable Home Tab

**Add Slash Commands:**
- Go to **Slash Commands**
- Create: `/bot-help`, `/bot-stats`, `/bot-clear`

### Step 5: Configure Environment (1 minute)

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env`:
```
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_APP_TOKEN=xapp-your-token-here
SLACK_SIGNING_SECRET=your-secret-here
```

(Get Signing Secret from Basic Information → App Credentials)

### Step 6: Add Knowledge Base (Optional)

```bash
mkdir knowledge_base
```

Copy `sample_faq.txt` to `knowledge_base/`:
```bash
cp sample_faq.txt knowledge_base/
```

Add your own documents (PDF, DOCX, TXT)

### Step 7: Run the Bot!

Make sure Ollama is running:
```bash
ollama serve
```

In another terminal, start bot:
```bash
python slack_bot.py
```

## ✅ Test It!

1. Open Slack
2. Send DM to your bot: "Hello!"
3. Or mention in channel: "@BotName what's your refund policy?"

## 🎯 Common Commands

**In Slack:**
- `@BotName [question]` - Ask in a channel
- Direct message - Just type your question
- `/bot-help` - Show help
- `/bot-stats` - View stats
- `/bot-clear` - Clear history

## 🐛 Quick Troubleshooting

**Bot not responding?**
```bash
# Check Ollama is running
ollama list

# Check bot is running
python slack_bot.py
```

**Model not found?**
```bash
ollama pull llama3.2:3b
```

**Import errors?**
```bash
pip install -r requirements.txt --upgrade
```

## 📁 File Structure

```
your-project/
├── slack_bot.py              ← Main bot
├── knowledge_base_manager.py ← Search engine
├── llama_ai.py              ← AI handler
├── .env                     ← Your secrets
├── knowledge_base/          ← Your documents
│   └── sample_faq.txt
└── requirements.txt
```

## 🎨 Customization

**Change AI Model:**
Edit `.env`:
```
OLLAMA_MODEL=llama3.1:8b
```

Then: `ollama pull llama3.1:8b`

**More search results:**
In `slack_bot.py`, line ~52:
```python
context = kb.search(text, n_results=5)  # Change 3 to 5
```

## 📚 Full Documentation

See `README.md` for complete documentation!

---

**Need Help?**
- Check README.md
- Review Slack app settings
- Ensure Ollama is running
- Check .env tokens are correct
