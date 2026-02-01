#!/usr/bin/env python3
"""
Test script to verify all components are working correctly.
Run this before starting the Slack bot to ensure everything is set up properly.
"""

import sys
import os
from dotenv import load_dotenv

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BOLD}{'='*50}{RESET}")
    print(f"{BOLD}{text}{RESET}")
    print(f"{BOLD}{'='*50}{RESET}\n")

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"{GREEN}✓ Python {version.major}.{version.minor}.{version.micro} detected{RESET}")
        return True
    else:
        print(f"{RED}✗ Python 3.8+ required, but {version.major}.{version.minor} found{RESET}")
        return False

def check_imports():
    """Check if all required packages are installed."""
    print("\nChecking Python packages...")
    required_packages = [
        ('slack_bolt', 'Slack Bolt'),
        ('dotenv', 'python-dotenv'),
        ('ollama', 'Ollama'),
        ('chromadb', 'ChromaDB'),
        ('sentence_transformers', 'Sentence Transformers'),
        ('PyPDF2', 'PyPDF2'),
        ('docx', 'python-docx'),
    ]
    
    all_installed = True
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"{GREEN}✓ {name} installed{RESET}")
        except ImportError:
            print(f"{RED}✗ {name} not installed{RESET}")
            all_installed = False
    
    return all_installed

def check_env_file():
    """Check if .env file exists and has required variables."""
    print("\nChecking environment configuration...")
    
    if not os.path.exists('.env'):
        print(f"{RED}✗ .env file not found{RESET}")
        print(f"{YELLOW}  Copy .env.example to .env and fill in your values{RESET}")
        return False
    
    load_dotenv()
    
    required_vars = [
        'SLACK_BOT_TOKEN',
        'SLACK_APP_TOKEN',
        'SLACK_SIGNING_SECRET'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if not value or 'your-' in value or 'here' in value:
            print(f"{RED}✗ {var} not configured{RESET}")
            all_set = False
        else:
            # Show partial value for security
            masked = value[:10] + '...' if len(value) > 10 else value
            print(f"{GREEN}✓ {var} configured ({masked}){RESET}")
    
    return all_set

def check_ollama():
    """Check if Ollama is installed and running."""
    print("\nChecking Ollama...")
    
    try:
        import ollama
        
        # Check if Ollama is running
        try:
            models = ollama.list()
            print(f"{GREEN}✓ Ollama is running{RESET}")
            
            # Check if model is downloaded
            model_name = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
            available_models = [m['name'] for m in models.get('models', [])]
            
            if any(model_name in m for m in available_models):
                print(f"{GREEN}✓ Model {model_name} is available{RESET}")
                return True
            else:
                print(f"{YELLOW}⚠ Model {model_name} not found{RESET}")
                print(f"{YELLOW}  Run: ollama pull {model_name}{RESET}")
                print(f"{YELLOW}  Available models: {', '.join(available_models)}{RESET}")
                return False
                
        except Exception as e:
            print(f"{RED}✗ Ollama is not running{RESET}")
            print(f"{YELLOW}  Start it with: ollama serve{RESET}")
            return False
            
    except ImportError:
        print(f"{RED}✗ Ollama package not installed{RESET}")
        return False

def check_knowledge_base():
    """Check if knowledge base directory exists."""
    print("\nChecking knowledge base...")
    
    kb_path = os.getenv('KNOWLEDGE_BASE_PATH', './knowledge_base')
    
    if not os.path.exists(kb_path):
        print(f"{YELLOW}⚠ Knowledge base directory not found{RESET}")
        print(f"{YELLOW}  Creating directory: {kb_path}{RESET}")
        os.makedirs(kb_path)
        print(f"{GREEN}✓ Knowledge base directory created{RESET}")
        print(f"{YELLOW}  Add your documents (PDF, DOCX, TXT) to this folder{RESET}")
        return True
    
    # Check if there are any documents
    files = [f for f in os.listdir(kb_path) if f.endswith(('.pdf', '.docx', '.txt'))]
    
    if files:
        print(f"{GREEN}✓ Knowledge base directory exists with {len(files)} document(s){RESET}")
        for f in files[:5]:  # Show first 5 files
            print(f"  - {f}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")
    else:
        print(f"{YELLOW}⚠ Knowledge base directory is empty{RESET}")
        print(f"{YELLOW}  Add some documents to improve bot responses{RESET}")
    
    return True

def test_knowledge_base():
    """Test the knowledge base functionality."""
    print("\nTesting knowledge base functionality...")
    
    try:
        from knowledge_base_manager import KnowledgeBase
        
        kb_path = os.getenv('KNOWLEDGE_BASE_PATH', './knowledge_base')
        kb = KnowledgeBase(kb_path)
        
        # Add a test document
        kb.add_text("This is a test document for the Slack bot.", 
                   metadata={"source": "test.txt", "type": "test"})
        
        # Search for it
        results = kb.search("test document")
        
        if results and len(results) > 0:
            print(f"{GREEN}✓ Knowledge base search is working{RESET}")
            stats = kb.get_stats()
            print(f"  Total documents: {stats['total_documents']}")
            return True
        else:
            print(f"{RED}✗ Knowledge base search returned no results{RESET}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Knowledge base test failed: {e}{RESET}")
        return False

def test_llama():
    """Test Llama AI functionality."""
    print("\nTesting Llama AI...")
    
    try:
        from llama_ai import LlamaAI
        
        llama = LlamaAI(
            model=os.getenv('OLLAMA_MODEL', 'llama3.2:3b'),
            base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        )
        
        # Test simple query
        response = llama.generate_response("Say 'test successful' if you can read this.")
        
        if response and len(response) > 0:
            print(f"{GREEN}✓ Llama AI is responding{RESET}")
            print(f"  Response: {response[:100]}...")
            return True
        else:
            print(f"{RED}✗ Llama AI returned empty response{RESET}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Llama AI test failed: {e}{RESET}")
        return False

def main():
    print_header("Slack AI Bot - System Check")
    
    results = []
    
    results.append(('Python Version', check_python_version()))
    results.append(('Python Packages', check_imports()))
    results.append(('Environment Config', check_env_file()))
    results.append(('Ollama Service', check_ollama()))
    results.append(('Knowledge Base', check_knowledge_base()))
    results.append(('Knowledge Base Test', test_knowledge_base()))
    results.append(('Llama AI Test', test_llama()))
    
    print_header("Test Results Summary")
    
    for name, passed in results:
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"{name:.<40} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print()
    if all_passed:
        print(f"{GREEN}{BOLD}✓ All tests passed! You're ready to run the bot.{RESET}")
        print(f"\n{YELLOW}Run the bot with: python slack_bot.py{RESET}")
    else:
        print(f"{RED}{BOLD}✗ Some tests failed. Please fix the issues above.{RESET}")
        print(f"\n{YELLOW}Check README.md for troubleshooting help.{RESET}")
    
    print()

if __name__ == "__main__":
    main()
