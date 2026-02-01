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

# Initialize Slack app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Initialize AI and Knowledge Base
logger.info("Initializing Knowledge Base...")
kb = KnowledgeBase(knowledge_base_path=os.environ.get("KNOWLEDGE_BASE_PATH", "./knowledge_base"))

logger.info("Loading documents from knowledge base folder...")
kb.load_documents_from_folder(os.environ.get("KNOWLEDGE_BASE_PATH", "./knowledge_base"))

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
        
        # Remove bot mention from text
        bot_user_id = client.auth_test()['user_id']
        text = re.sub(f'<@{bot_user_id}>', '', text).strip()
        
        if not text:
            say("Hi! How can I help you today?")
            return
        
        # Show typing indicator
        client.chat_postMessage(
            channel=channel_id,
            text=f"<@{user_id}> Let me think about that... 🤔"
        )
        
        # Search knowledge base
        logger.info(f"Searching knowledge base for: {text}")
        context = kb.search(text, n_results=3)
        
        # Generate response
        logger.info(f"Generating response for user {user_id}")
        response = llama.generate_response(
            query=text,
            context=context,
            user_id=user_id,
            use_history=True
        )
        
        # Add context indicator if knowledge base was used
        if context and len(context) > 0:
            sources = list(set([ctx.get('metadata', {}).get('source', 'Unknown') 
                              for ctx in context if ctx.get('metadata', {}).get('source')]))
            if sources:
                response += f"\n\n_📚 Sources: {', '.join(sources)}_"
        
        # Send response
        say(f"<@{user_id}> {response}")
        
    except Exception as e:
        logger.error(f"Error handling mention: {e}")
        say(f"Sorry, I encountered an error: {str(e)}")


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
        
        # Search knowledge base
        logger.info(f"DM - Searching knowledge base for: {text}")
        context = kb.search(text, n_results=3)
        
        # Generate response
        logger.info(f"DM - Generating response for user {user_id}")
        response = llama.generate_response(
            query=text,
            context=context,
            user_id=user_id,
            use_history=True
        )
        
        # Add context indicator
        if context and len(context) > 0:
            sources = list(set([ctx.get('metadata', {}).get('source', 'Unknown') 
                              for ctx in context if ctx.get('metadata', {}).get('source')]))
            if sources:
                response += f"\n\n_📚 Sources: {', '.join(sources)}_"
        
        # Send response
        say(response)
        
    except Exception as e:
        logger.error(f"Error handling DM: {e}")
        say(f"Sorry, I encountered an error: {str(e)}")


# Slash command: /bot-help
@app.command("/bot-help")
def handle_help_command(ack, respond):
    """Show help information."""
    ack()
    help_text = """
*🤖 Slack Bot Help*

*How to use:*
• Mention me in a channel: `@BotName your question`
• Send me a direct message with your question
• I'll search my knowledge base and provide relevant answers

*Commands:*
• `/bot-help` - Show this help message
• `/bot-stats` - Show knowledge base statistics
• `/bot-clear` - Clear your conversation history

*Features:*
• Context-aware conversations (I remember recent messages)
• Knowledge base search with source citations
• Powered by Llama AI 🦙
    """
    respond(help_text)


# Slash command: /bot-stats
@app.command("/bot-stats")
def handle_stats_command(ack, respond):
    """Show knowledge base statistics."""
    ack()
    stats = kb.get_stats()
    stats_text = f"""
*📊 Bot Statistics*

• Total documents in knowledge base: *{stats['total_documents']}*
• Collection name: `{stats['collection_name']}`
• AI Model: `{llama.model}`
    """
    respond(stats_text)


# Slash command: /bot-clear
@app.command("/bot-clear")
def handle_clear_command(ack, respond, command):
    """Clear conversation history for the user."""
    ack()
    user_id = command['user_id']
    llama.clear_history(user_id)
    respond("✅ Your conversation history has been cleared!")


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
