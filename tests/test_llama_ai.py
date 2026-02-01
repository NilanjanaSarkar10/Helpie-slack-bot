"""Unit tests for llama_ai.py"""
import unittest
from unittest.mock import Mock, patch
from llama_ai import LlamaAI


class TestLlamaAI(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        with patch('llama_ai.ollama.Client'):
            self.llama = LlamaAI(model="test-model", base_url="http://test:11434")
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        # Test control character removal
        dirty = "Hello\x00World\x1f"
        clean = LlamaAI._sanitize_input(dirty)
        self.assertEqual(clean, "HelloWorld")
        
        # Test length limiting
        long_text = "a" * 20000
        clean = LlamaAI._sanitize_input(long_text)
        self.assertEqual(len(clean), 10000)
    
    def test_sanitize_error(self):
        """Test error message sanitization."""
        # Test path removal
        error = Exception("Error in /path/to/file.py")
        sanitized = LlamaAI._sanitize_error(error)
        self.assertNotIn("/path/to/file.py", sanitized)
        
        # Test connection error
        error = Exception("Connection refused")
        sanitized = LlamaAI._sanitize_error(error)
        self.assertEqual(sanitized, "Unable to connect to the AI service")
    
    def test_build_prompt_no_context(self):
        """Test prompt building without context."""
        prompt = self.llama._build_prompt("What is Python?", context=None)
        self.assertIn("What is Python?", prompt)
        self.assertIn("general knowledge", prompt)
    
    def test_build_prompt_with_context(self):
        """Test prompt building with context."""
        context = [
            {
                'content': 'Python is a programming language',
                'metadata': {'source': 'python.txt'}
            }
        ]
        prompt = self.llama._build_prompt("What is Python?", context=context)
        self.assertIn("Python is a programming language", prompt)
        self.assertIn("python.txt", prompt)
        self.assertIn("KNOWLEDGE BASE CONTEXT", prompt)
    
    @patch('llama_ai.ollama.Client')
    def test_generate_response_sanitizes_input(self, mock_client):
        """Test that generate_response sanitizes input."""
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.chat.return_value = {
            'message': {'content': 'Test response'}
        }
        
        llama = LlamaAI()
        # Try with control characters
        response = llama.generate_response("Hello\x00World")
        # Should not raise an error and should sanitize
        self.assertIsNotNone(response)


if __name__ == '__main__':
    unittest.main()
