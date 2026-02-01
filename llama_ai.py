import ollama
import logging
import os
import re
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LlamaAI:
    """Handles interactions with Llama AI through Ollama."""
    
    def __init__(self, model: str = "llama3.2:3b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.conversation_history = {}
        
        # Create client with custom base_url (FIX: actually use the parameter)
        self.client = ollama.Client(host=base_url)
        
        # Test connection
        try:
            self.client.list()
            logger.info(f"Connected to Ollama at {base_url}. Using model: {model}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama at {base_url}: {e}")
            logger.error("Make sure Ollama is installed and running!")
    
    @staticmethod
    def _sanitize_input(text: str) -> str:
        """Sanitize user input to prevent log injection and other issues."""
        if not text:
            return ""
        # Remove control characters and limit length
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        return sanitized[:10000]  # Max 10k chars
    
    @staticmethod
    def _sanitize_error(error: Exception) -> str:
        """Sanitize error messages to not leak internals."""
        error_str = str(error)
        # Remove file paths
        error_str = re.sub(r'/[^\s]+', '[path]', error_str)
        # Generic message for common errors
        if 'connection' in error_str.lower():
            return "Unable to connect to the AI service"
        if 'timeout' in error_str.lower():
            return "Request timed out"
        return "An error occurred while processing your request"
    
    def generate_response(
        self, 
        query: str, 
        context: List[Dict] = None,
        user_id: str = None,
        use_history: bool = True
    ) -> str:
        """Generate a response using Llama with optional context and conversation history."""
        
        # Sanitize input
        query = self._sanitize_input(query)
        if not query:
            return "I didn't receive a valid question."
        
        # Build the prompt with context
        prompt = self._build_prompt(query, context)

        # Get conversation history for this user
        messages = []

        # Add system message that allows mixing KB and general knowledge
        system_content = (
            "You are a helpful assistant with access to a knowledge base and general knowledge.\n"
            "INSTRUCTIONS:\n"
            "- Prioritize information from the knowledge base when available\n"
            "- You MAY supplement KB information with your general knowledge to provide complete, helpful answers\n"
            "- For information from the KB, cite the source in square brackets like [Source: EMP_PM.pdf]\n"
            "- For general knowledge, you don't need to cite, but be clear when you're adding context beyond the KB\n"
            "- Be direct and concise\n"
            "- If the KB has partial information, use it and fill in gaps with general knowledge\n"
            "- If the KB has no information, provide a helpful answer from general knowledge\n"
        )

        messages.append({'role': 'system', 'content': system_content})
        
        if use_history and user_id and user_id in self.conversation_history:
            messages.extend(self.conversation_history[user_id][-6:])  # Last 3 exchanges
        
        # Add current query
        messages.append({
            'role': 'user',
            'content': prompt
        })
        
        try:
            # Generate response with moderate temperature for natural answers
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': 0.3,  # Moderate temperature for natural but factual responses
                    'top_p': 0.9,
                    'repeat_penalty': 1.1
                }
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
            return self._sanitize_error(e)
    
    def _build_prompt(self, query: str, context: List[Dict] = None) -> str:
        """Build a prompt with context from knowledge base."""
        
        if not context or len(context) == 0:
            return f"""No relevant context was found in the knowledge base.

Question: {query}

Please provide a helpful answer using your general knowledge."""
        
        # Build context string with clear separation
        context_str = "=== KNOWLEDGE BASE CONTEXT ===\n\n"
        for i, ctx in enumerate(context, 1):
            source = ctx.get('metadata', {}).get('source', 'Unknown')
            content = ctx.get('content', '')
            context_str += f"--- Document {i} (Source: {source}) ---\n{content}\n\n"
        
        context_str += "=== END OF CONTEXT ===\n\n"
        
        # Build prompt that enforces KB-ONLY answers
        prompt = f"""{context_str}

IMPORTANT INSTRUCTIONS:
1. ONLY use information from the knowledge base above
2. Do NOT use general knowledge, do NOT supplement with outside information
3. Always cite the source document like [Source: FILENAME] when referencing KB content
4. If you cannot find the answer in the knowledge base, respond: "I don't have information about this in the available documentation."
5. Be direct and concise

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
            models = self.client.list()
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
            self.client.pull(self.model)
            logger.info(f"Model {self.model} downloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False
