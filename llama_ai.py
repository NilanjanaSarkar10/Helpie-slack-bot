import ollama
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LlamaAI:
    """Handles interactions with Llama AI through Ollama."""
    
    def __init__(self, model: str = "llama3.2:3b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.conversation_history = {}
        
        # Test connection
        try:
            ollama.list()
            logger.info(f"Connected to Ollama successfully. Using model: {model}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            logger.error("Make sure Ollama is installed and running!")
    
    def generate_response(
        self, 
        query: str, 
        context: List[Dict] = None,
        user_id: str = None,
        use_history: bool = True
    ) -> str:
        """Generate a response using Llama with optional context and conversation history."""
        
        # Build the prompt with context
        prompt = self._build_prompt(query, context)
        
        # Get conversation history for this user
        messages = []
        if use_history and user_id and user_id in self.conversation_history:
            messages = self.conversation_history[user_id][-6:]  # Last 3 exchanges
        
        # Add current query
        messages.append({
            'role': 'user',
            'content': prompt
        })
        
        try:
            # Generate response
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            
            assistant_message = response['message']['content']
            
            # Store in conversation history
            if user_id:
                if user_id not in self.conversation_history:
                    self.conversation_history[user_id] = []
                
                self.conversation_history[user_id].append({
                    'role': 'user',
                    'content': query  # Store original query, not the full prompt
                })
                self.conversation_history[user_id].append({
                    'role': 'assistant',
                    'content': assistant_message
                })
                
                # Keep only last 10 messages (5 exchanges)
                if len(self.conversation_history[user_id]) > 10:
                    self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Sorry, I encountered an error processing your request: {str(e)}"
    
    def _build_prompt(self, query: str, context: List[Dict] = None) -> str:
        """Build a prompt with context from knowledge base."""
        
        if not context or len(context) == 0:
            return query
        
        # Build context string
        context_str = "Here is some relevant information from the knowledge base:\n\n"
        for i, ctx in enumerate(context, 1):
            source = ctx.get('metadata', {}).get('source', 'Unknown')
            content = ctx.get('content', '')
            context_str += f"[Source {i}: {source}]\n{content}\n\n"
        
        # Build full prompt
        prompt = f"""{context_str}

Based on the above information, please answer the following question. If the information provided doesn't contain the answer, say so and provide the best answer you can based on your general knowledge.

Question: {query}

Answer:"""
        
        return prompt
    
    def clear_history(self, user_id: str = None):
        """Clear conversation history for a user or all users."""
        if user_id:
            if user_id in self.conversation_history:
                del self.conversation_history[user_id]
                logger.info(f"Cleared history for user {user_id}")
        else:
            self.conversation_history = {}
            logger.info("Cleared all conversation history")
    
    def check_model_availability(self) -> bool:
        """Check if the specified model is available."""
        try:
            models = ollama.list()
            available_models = [model['name'] for model in models.get('models', [])]
            
            # Check if our model is in the list
            model_available = any(self.model in model for model in available_models)
            
            if not model_available:
                logger.warning(f"Model {self.model} not found. Available models: {available_models}")
                logger.info(f"To download the model, run: ollama pull {self.model}")
            else:
                logger.info(f"Model {self.model} is available")
            
            return model_available
            
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False
    
    def pull_model(self):
        """Pull/download the specified model."""
        try:
            logger.info(f"Pulling model {self.model}... This may take a while.")
            ollama.pull(self.model)
            logger.info(f"Model {self.model} downloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False
