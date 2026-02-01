# ✅ COMPLETE SETUP CHECKLIST

Follow this checklist to get your Slack AI bot running!

## Phase 1: Install Software (10 minutes)

### 1.1 Install Python ✓
- [ ] Download Python 3.8+ from python.org
- [ ] Verify: Run `python --version` or `python3 --version`
- [ ] Should show version 3.8 or higher

### 1.2 Install Ollama ✓
- [ ] **Windows:** Download from https://ollama.ai/download/windows
- [ ] **Mac:** Run `brew install ollama`
- [ ] **Linux:** Run `curl -fsSL https://ollama.ai/install.sh | sh`
- [ ] Verify: Run `ollama --version`

### 1.3 Download AI Model ✓
- [ ] Start Ollama: `ollama serve`
- [ ] In new terminal: `ollama pull llama3.2:3b`
- [ ] Wait for download (takes 2-5 minutes, ~2GB)
- [ ] Verify: `ollama list` should show llama3.2:3b

## Phase 2: Set Up Project (5 minutes)

### 2.1 Create Project Folder ✓
- [ ] Create folder: `mkdir slack-ai-bot`
- [ ] Navigate: `cd slack-ai-bot`
- [ ] Extract all files from the download here

### 2.2 Install Python Dependencies ✓
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

- [ ] Virtual environment created
- [ ] All packages installed successfully

## Phase 3: Create Slack App (10 minutes)

### 3.1 Create the App ✓
- [ ] Go to https://api.slack.com/apps
- [ ] Click "Create New App" → "From scratch"
- [ ] Name it (e.g., "AI Assistant")
- [ ] Select your workspace
- [ ] Click "Create App"

### 3.2 Configure OAuth Scopes ✓
- [ ] Go to "OAuth & Permissions" in sidebar
- [ ] Scroll to "Bot Token Scopes"
- [ ] Click "Add an OAuth Scope" and add these:
  - [ ] `app_mentions:read`
  - [ ] `chat:write`
  - [ ] `im:history`
  - [ ] `im:read`
  - [ ] `im:write`
  - [ ] `channels:history`
  - [ ] `groups:history`
  - [ ] `mpim:history`

### 3.3 Install to Workspace ✓
- [ ] Scroll up to "OAuth Tokens for Your Workspace"
- [ ] Click "Install to Workspace"
- [ ] Click "Allow"
- [ ] **COPY** the "Bot User OAuth Token" (starts with xoxb-)
- [ ] Save it somewhere safe!

### 3.4 Enable Socket Mode ✓
- [ ] Go to "Socket Mode" in sidebar
- [ ] Toggle "Enable Socket Mode" to ON
- [ ] Click "Generate an app-level token"
- [ ] Token name: `socket_token`
- [ ] Add scope: `connections:write`
- [ ] Click "Generate"
- [ ] **COPY** the token (starts with xapp-)
- [ ] Click "Done"

### 3.5 Subscribe to Events ✓
- [ ] Go to "Event Subscriptions"
- [ ] Toggle "Enable Events" to ON
- [ ] Expand "Subscribe to bot events"
- [ ] Click "Add Bot User Event" and add:
  - [ ] `app_mention`
  - [ ] `message.im`
- [ ] Click "Save Changes" at bottom

### 3.6 Enable Home Tab ✓
- [ ] Go to "App Home"
- [ ] Under "Show Tabs", toggle "Home Tab" to ON
- [ ] Check "Allow users to send Slash commands and messages"

### 3.7 Add Slash Commands ✓
- [ ] Go to "Slash Commands"
- [ ] Click "Create New Command" for each:
  
  Command 1:
  - [ ] Command: `/bot-help`
  - [ ] Short Description: `Show bot help`
  - [ ] Save
  
  Command 2:
  - [ ] Command: `/bot-stats`
  - [ ] Short Description: `Show knowledge base statistics`
  - [ ] Save
  
  Command 3:
  - [ ] Command: `/bot-clear`
  - [ ] Short Description: `Clear conversation history`
  - [ ] Save

### 3.8 Get Signing Secret ✓
- [ ] Go to "Basic Information"
- [ ] Under "App Credentials"
- [ ] **COPY** the "Signing Secret"

## Phase 4: Configure Bot (5 minutes)

### 4.1 Create .env File ✓
- [ ] Copy `.env.example` to `.env`
  - Windows: `copy .env.example .env`
  - Mac/Linux: `cp .env.example .env`

### 4.2 Fill in Tokens ✓
- [ ] Open `.env` in text editor (Notepad, VS Code, etc.)
- [ ] Replace values:
  ```
  SLACK_BOT_TOKEN=xoxb-paste-your-token-here
  SLACK_APP_TOKEN=xapp-paste-your-token-here
  SLACK_SIGNING_SECRET=paste-your-secret-here
  ```
- [ ] Save the file

### 4.3 Add Knowledge Base Documents ✓
- [ ] Create folder: `mkdir knowledge_base`
- [ ] Copy `sample_faq.txt` into it:
  - Windows: `copy sample_faq.txt knowledge_base\`
  - Mac/Linux: `cp sample_faq.txt knowledge_base/`
- [ ] Add your own documents (PDF, DOCX, TXT files)
- [ ] Examples:
  - Company policies
  - Product documentation
  - FAQs
  - Training materials

## Phase 5: Test & Launch (5 minutes)

### 5.1 Test Installation ✓
- [ ] Run test script: `python test_setup.py`
- [ ] All tests should PASS
- [ ] If any fail, fix issues before continuing

### 5.2 Start Ollama ✓
- [ ] In one terminal: `ollama serve`
- [ ] Keep this running
- [ ] You should see "Ollama is running"

### 5.3 Start the Bot ✓
- [ ] In new terminal, activate venv:
  - Windows: `venv\Scripts\activate`
  - Mac/Linux: `source venv/bin/activate`
- [ ] Run: `python slack_bot.py`
- [ ] Should see:
  ```
  INFO - Starting Slack bot in Socket Mode...
  INFO - Knowledge Base: X documents loaded
  ⚡️ Bolt app is running!
  ```

### 5.4 Test in Slack ✓
- [ ] Open Slack workspace
- [ ] Find your bot in Apps
- [ ] Send DM: "Hello!"
- [ ] Bot should respond
- [ ] In a channel, mention: `@BotName what's your refund policy?`
- [ ] Bot should respond with answer + sources
- [ ] Try slash command: `/bot-help`

## Phase 6: Customize (Optional)

### 6.1 Change Bot Name/Icon ✓
- [ ] Go to Slack App settings
- [ ] "Basic Information" → "Display Information"
- [ ] Update name, icon, description
- [ ] Save

### 6.2 Add More Documents ✓
- [ ] Add PDFs, DOCX, TXT to `knowledge_base/`
- [ ] Restart bot to load new documents

### 6.3 Try Different Models ✓
- [ ] Edit `.env`: Change `OLLAMA_MODEL`
- [ ] Download new model: `ollama pull model-name`
- [ ] Restart bot

Options:
- `llama3.2:1b` - Fastest
- `llama3.2:3b` - Recommended ✓
- `llama3.1:8b` - Best quality

## Common Issues & Solutions

### ❌ Bot doesn't respond
- [ ] Check Ollama is running: `ollama list`
- [ ] Check bot is running in terminal
- [ ] Verify tokens in `.env` are correct
- [ ] Check Slack app has correct permissions

### ❌ "Model not found" error
- [ ] Run: `ollama pull llama3.2:3b`
- [ ] Wait for download
- [ ] Restart bot

### ❌ Import errors
- [ ] Activate virtual environment
- [ ] Run: `pip install -r requirements.txt --upgrade`

### ❌ Knowledge base empty
- [ ] Check `knowledge_base/` folder exists
- [ ] Add .pdf, .docx, or .txt files
- [ ] Restart bot

### ❌ Connection refused
- [ ] Make sure Ollama is running: `ollama serve`
- [ ] Check if port 11434 is available

## Success Indicators

You know everything is working when:
- [x] Test script shows all PASS
- [x] Bot responds to DMs
- [x] Bot responds to @mentions in channels
- [x] Slash commands work
- [x] Bot cites knowledge base sources
- [x] No errors in terminal

## Next Steps

Once everything works:
1. Add more knowledge base documents
2. Customize bot responses
3. Train your team to use it
4. Monitor and improve
5. Share feedback!

## Support Resources

- **README.md** - Complete documentation
- **QUICKSTART.md** - 5-minute setup guide
- **ARCHITECTURE.md** - How it works
- **test_setup.py** - Diagnostic tool

## Quick Reference

**Start bot:**
```bash
# Terminal 1
ollama serve

# Terminal 2
source venv/bin/activate  # or venv\Scripts\activate on Windows
python slack_bot.py
```

**Stop bot:**
- Press `Ctrl+C` in bot terminal
- Press `Ctrl+C` in Ollama terminal

**Restart bot:**
- Stop bot
- Make changes
- Start bot again

**Add documents:**
1. Add files to `knowledge_base/`
2. Restart bot
3. Documents auto-load on startup

---

## 🎉 Congratulations!

If you've completed this checklist, you now have a fully functional AI-powered Slack bot with a custom knowledge base! 

**Enjoy your new AI assistant!** 🤖✨
