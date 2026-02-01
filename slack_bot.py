import os
import re
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from knowledge_base_manager import KnowledgeBase
from llama_ai import LlamaAI
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Optional: force searches to a specific collection (e.g., 'springworks')
FORCE_KB_COLLECTION = os.environ.get("FORCE_KB_COLLECTION")
# Default collection to use when no specific intent is detected
DEFAULT_COLLECTION = os.environ.get("DEFAULT_KB_COLLECTION", "springworks")

# Category-specific keywords for intelligent routing
EMPLOYMENT_KEYWORDS = [
    'employment', 'employ', 'work', 'reference', 'candidate', 'hr', 'company',
    'last working', 'working date', 'designation', 'salary', 'relieving',
    'experience letter', 'joining date', 'tenure', 'employee', 'payslip',
    'employment contract', 'offer letter', 'overlap', 'concurrent', 'overlap check'
]

EDUCATION_KEYWORDS = [
    'education', 'degree', 'university', 'college', 'certificate', 'school',
    'diploma', 'graduation', 'credential', 'academic', 'institution', 'course',
    'marks', 'transcript', 'major', 'minor', 'license', 'certification'
]

ADDRESS_KEYWORDS = [
    'dav', 'pav', 'cav', 'address', 'digital address', 'present address', 
    'current address', 'permanent address', 'address verification', 'postal',
    'location', 'residence'
]

CRIMINAL_KEYWORDS = [
    'criminal', 'court', 'case', 'record', 'database', 'conviction',
    'arrest', 'prosecution', 'legal', 'jail', 'prison', 'offense', 'felony'
]

IDENTITY_KEYWORDS = [
    'identity', 'id', 'aadhar', 'pan', 'passport', 'driving license',
    'government id', 'voter id', 'ssn', 'tax id', 'identification'
]

# All verification keywords (for backward compatibility)
VERIFICATION_KEYWORDS = (
    EMPLOYMENT_KEYWORDS + EDUCATION_KEYWORDS + ADDRESS_KEYWORDS + 
    CRIMINAL_KEYWORDS + IDENTITY_KEYWORDS + 
    ['verification', 'verify', 'screening', 'checks', 'background',
     'green', 'red', 'amber', 'discrepancy', 'mismatch', 'match',
     'verified', 'unverified', 'pending', 'completed', 'insufficient']
)


def sanitize_for_logging(text: str) -> str:
    """Sanitize user input before logging to prevent log injection."""
    if not text:
        return ""
    # Remove control characters and newlines
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # Limit length for logs
    return sanitized[:200] + "..." if len(sanitized) > 200 else sanitized


def detect_collection_for_query(text: str) -> str | None:
    """Intelligently detect the document category from query keywords.
    
    Routes to specific collections based on keywords:
    - If employment keywords found → search EMP_PM.pdf (employment verification)
    - If education keywords found → search Education_PM.pdf (education verification)
    - If address keywords found → search ADD_PM.pdf (address verification)
    - If criminal keywords found → search MISC_PM.pdf (red flags/criminal checks)
    - If identity keywords found → search MISC_PM.pdf (identity verification)
    - Default → springworks (all docs)
    
    Returns: 'springworks' to search all springworks docs in the collection
    """
    if not text:
        return DEFAULT_COLLECTION

    lowered = text.lower()
    
    # Count keyword matches per category
    employment_count = sum(1 for kw in EMPLOYMENT_KEYWORDS if kw in lowered)
    education_count = sum(1 for kw in EDUCATION_KEYWORDS if kw in lowered)
    address_count = sum(1 for kw in ADDRESS_KEYWORDS if kw in lowered)
    criminal_count = sum(1 for kw in CRIMINAL_KEYWORDS if kw in lowered)
    identity_count = sum(1 for kw in IDENTITY_KEYWORDS if kw in lowered)
    
    # Determine dominant category
    counts = {
        'employment': employment_count,
        'education': education_count,
        'address': address_count,
        'criminal': criminal_count,
        'identity': identity_count
    }
    
    dominant = max(counts, key=counts.get)
    
    # If a category has at least 1 match, use it
    if counts[dominant] > 0:
        logger.info(f"Query category detected: {dominant} (keywords: {counts[dominant]})")
        return DEFAULT_COLLECTION  # Still use springworks, will be filtered by semantic search
    
    # If no keywords matched, use default collection
    return DEFAULT_COLLECTION


def build_response_blocks(response: str, context: list, user_id: str = None) -> list:
    """Build Slack Block Kit response with optional source citations.
    
    Args:
        response: The bot's response text
        context: List of context documents from knowledge base
        user_id: Optional user ID to mention
    
    Returns:
        List of Slack blocks
    """
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<@{user_id}> {response}" if user_id else response
            }
        }
    ]
    
    # Add context indicator if knowledge base was used
    if context and len(context) > 0:
        sources = list(set([ctx.get('metadata', {}).get('source', 'Unknown') 
                          for ctx in context if ctx.get('metadata', {}).get('source')]))
        if sources:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📚 *Sources:* {', '.join(sources)}"
                    }
                ]
            })
    
    return blocks


def build_error_blocks(user_id: str = None) -> list:
    """Build generic error response blocks (don't leak internals).
    
    Args:
        user_id: Optional user ID to mention
    
    Returns:
        List of Slack blocks
    """
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<@{user_id}> ⚠️ Oops! Something went wrong." if user_id else "⚠️ Oops! Something went wrong."
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "_Please try again or contact support if the issue persists._"
                }
            ]
        }
    ]

# Initialize Slack app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Initialize AI and Knowledge Base
logger.info("Initializing Knowledge Base...")
KB_PATH = os.environ.get("KNOWLEDGE_BASE_PATH", "./knowledge_base")
kb = KnowledgeBase(knowledge_base_path=KB_PATH)

logger.info("Loading documents from knowledge base folder...")
kb.load_documents_from_folder(KB_PATH)

# If a specific collection is forced (e.g., Springworks), try loading that folder
if FORCE_KB_COLLECTION:
    collection_folder = os.path.join(KB_PATH, FORCE_KB_COLLECTION)
    if os.path.exists(collection_folder):
        logger.info(f"Loading forced collection: {FORCE_KB_COLLECTION}")
        kb.load_documents_from_folder(collection_folder, collection_name=FORCE_KB_COLLECTION)
    else:
        logger.warning(f"Forced collection folder not found: {collection_folder}")

logger.info("Initializing Llama AI...")
llama = LlamaAI(
    model=os.environ.get("OLLAMA_MODEL", "llama3.2:3b"),
    base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
)

# Check if model is available
if not llama.check_model_availability():
    logger.warning("Model not available. You may need to download it using: ollama pull llama3.2:3b")


# Event listener for app mentions
@app.event("app_mention")
def handle_mention(event, say, client):
    """Handle when the bot is mentioned in a channel."""
    try:
        # Get the message text and remove the bot mention
        text = event['text']
        user_id = event['user']
        channel_id = event['channel']
        thread_ts = event.get('thread_ts', event['ts'])  # Get thread timestamp
        
        # Remove bot mention from text
        bot_user_id = client.auth_test()['user_id']
        text = re.sub(f'<@{bot_user_id}>', '', text).strip()
        
        if not text:
            say(text="Hi! How can I help you today?", thread_ts=thread_ts)
            return
        
        # Show typing indicator in the thread
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=f"<@{user_id}> Searching knowledge base... 🔍"
        )
        
        # Decide which collection to search: forced override or intent detection
        collection_to_use = FORCE_KB_COLLECTION or detect_collection_for_query(text)
        
        # Detect category for smarter filtering
        lowered = text.lower()
        detected_category = None
        if sum(1 for kw in EMPLOYMENT_KEYWORDS if kw in lowered) > 0:
            detected_category = 'employment'
        elif sum(1 for kw in EDUCATION_KEYWORDS if kw in lowered) > 0:
            detected_category = 'education'
        elif sum(1 for kw in ADDRESS_KEYWORDS if kw in lowered) > 0:
            detected_category = 'address'
        elif sum(1 for kw in CRIMINAL_KEYWORDS if kw in lowered) > 0 or sum(1 for kw in IDENTITY_KEYWORDS if kw in lowered) > 0:
            detected_category = 'compliance'
        
        logger.info(f"Searching knowledge base for: {sanitize_for_logging(text)} (collection: {collection_to_use}, category: {detected_category})")
        context = kb.search(text, n_results=10, collection_name=collection_to_use, category=detected_category)
        
        # Generate response
        logger.info(f"Generating response for user {user_id}")
        response = llama.generate_response(
            query=text,
            context=context,
            user_id=user_id,
            use_history=True
        )
        
        # Build response blocks using helper
        blocks = build_response_blocks(response, context, user_id)
        
        # Send response in the thread with blocks
        say(blocks=blocks, text=f"<@{user_id}> {response[:100]}...", thread_ts=thread_ts)
        
    except Exception as e:
        logger.error(f"Error handling mention: {e}")
        say(blocks=build_error_blocks(user_id), text="Error", thread_ts=event.get('thread_ts', event['ts']))


# Event listener for direct messages
@app.event("message")
def handle_message(event, say, client):
    """Handle direct messages to the bot."""
    
    # Ignore bot messages and threaded messages
    if event.get('bot_id') or event.get('thread_ts'):
        return
    
    # Only respond to direct messages
    channel_type = event.get('channel_type')
    if channel_type != 'im':
        return
    
    try:
        text = event.get('text', '').strip()
        user_id = event['user']
        
        if not text:
            return
        
        # Search knowledge base with intent-based collection selection
        collection_to_use = FORCE_KB_COLLECTION or detect_collection_for_query(text)
        
        # Detect category for smarter filtering
        lowered = text.lower()
        detected_category = None
        if sum(1 for kw in EMPLOYMENT_KEYWORDS if kw in lowered) > 0:
            detected_category = 'employment'
        elif sum(1 for kw in EDUCATION_KEYWORDS if kw in lowered) > 0:
            detected_category = 'education'
        elif sum(1 for kw in ADDRESS_KEYWORDS if kw in lowered) > 0:
            detected_category = 'address'
        elif sum(1 for kw in CRIMINAL_KEYWORDS if kw in lowered) > 0 or sum(1 for kw in IDENTITY_KEYWORDS if kw in lowered) > 0:
            detected_category = 'compliance'
        
        logger.info(f"DM - Searching knowledge base for: {sanitize_for_logging(text)} (collection: {collection_to_use}, category: {detected_category})")
        context = kb.search(text, n_results=10, collection_name=collection_to_use, category=detected_category)
        
        # Generate response
        logger.info(f"DM - Generating response for user {user_id}")
        response = llama.generate_response(
            query=text,
            context=context,
            user_id=user_id,
            use_history=True
        )
        
        # Build response blocks using helper
        blocks = build_response_blocks(response, context)
        
        # Send response with blocks
        say(blocks=blocks, text=response[:100] + "..." if len(response) > 100 else response)
        
    except Exception as e:
        logger.error(f"Error handling DM: {e}")
        say(blocks=build_error_blocks(), text="Error")


# Slash command: /bot-help
@app.command("/bot-help")
def handle_help_command(ack, respond):
    """Show help information."""
    ack()
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🤖 Helpie Bot - Quick Guide"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*How to use:*\n• Mention me in a channel: `@Helpie your question`\n• Send me a direct message with your question\n• I'll search my knowledge base and provide crisp, relevant answers"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Available Commands:*\n• `/bot-help` - Show this help message\n• `/bot-stats` - View knowledge base statistics\n• `/bot-clear` - Clear your conversation history"
            }
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "✨ *Features:* Context-aware conversations • Knowledge base search • Source citations • Powered by Llama AI 🦙"
                }
            ]
        }
    ]
    respond(blocks=blocks, text="Helpie Bot Help")


# Slash command: /bot-stats
@app.command("/bot-stats")
def handle_stats_command(ack, respond):
    """Show knowledge base statistics."""
    ack()
    stats = kb.get_stats()
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📊 Bot Statistics"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Total Documents:*\n{stats['total_documents']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*AI Model:*\n`{llama.model}`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Collection:*\n`{stats['collection_name']}`"
                }
            ]
        }
    ]
    respond(blocks=blocks, text="Bot Statistics")


# Slash command: /bot-clear
@app.command("/bot-clear")
def handle_clear_command(ack, respond, command):
    """Clear conversation history for the user."""
    ack()
    user_id = command['user_id']
    llama.clear_history(user_id)
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✅ *Done!* Your conversation history has been cleared."
            }
        }
    ]
    respond(blocks=blocks, text="History cleared")


# Home tab
@app.event("app_home_opened")
def update_home_tab(client, event):
    """Update the app home tab."""
    try:
        stats = kb.get_stats()
        client.views_publish(
            user_id=event["user"],
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🤖 Welcome to Your AI Assistant"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*I'm here to help answer your questions!*\n\nI use a custom knowledge base and Llama AI to provide accurate, context-aware responses."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*📊 Knowledge Base Stats*\n• Documents: {stats['total_documents']}\n• AI Model: `{llama.model}`"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*💡 How to Use*\n• Mention me in any channel\n• Send me a direct message\n• Use `/bot-help` for more info"
                        }
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error updating home tab: {e}")


# Start the app
if __name__ == "__main__":
    # Verify required environment variables
    required_vars = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file")
        exit(1)
    
    logger.info("Starting Slack bot in Socket Mode...")
    logger.info(f"Knowledge Base: {kb.get_stats()['total_documents']} documents loaded")
    
    # Start the bot
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()