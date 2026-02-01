"""Unit tests for knowledge_base_manager.py"""
import unittest
import tempfile
import shutil
import os
from knowledge_base_manager import KnowledgeBase


class TestKnowledgeBase(unittest.TestCase):
    def setUp(self):
        """Create temporary directory for tests."""
        self.test_dir = tempfile.mkdtemp()
        self.kb = KnowledgeBase(knowledge_base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def test_add_text(self):
        """Test adding text to knowledge base."""
        self.kb.add_text("This is a test document.", metadata={"source": "test.txt"})
        self.assertGreater(len(self.kb.documents), 0)
        self.assertEqual(len(self.kb.documents), len(self.kb.embeddings))
    
    def test_search(self):
        """Test searching knowledge base."""
        self.kb.add_text("Python is a programming language.", metadata={"source": "python.txt"})
        self.kb.add_text("JavaScript is also a programming language.", metadata={"source": "js.txt"})
        
        results = self.kb.search("Python programming", n_results=1)
        self.assertEqual(len(results), 1)
        self.assertIn("Python", results[0]['content'])
    
    def test_keyword_boosting(self):
        """Test that keyword matching boosts search results."""
        self.kb.add_text("Employment verification process", metadata={"source": "emp.txt"})
        self.kb.add_text("Education verification process", metadata={"source": "edu.txt"})
        
        results = self.kb.search("employment", n_results=1)
        self.assertEqual(len(results), 1)
        # Should return employment doc due to keyword boost
        self.assertEqual(results[0]['metadata']['source'], 'emp.txt')
    
    def test_save_and_load(self):
        """Test saving and loading index."""
        self.kb.add_text("Test document", metadata={"source": "test.txt"})
        original_count = len(self.kb.documents)
        
        # Save
        self.kb._save_index()
        
        # Verify files exist
        metadata_path = os.path.join(self.test_dir, "metadata.json")
        embeddings_path = os.path.join(self.test_dir, "embeddings.npy")
        self.assertTrue(os.path.exists(metadata_path))
        self.assertTrue(os.path.exists(embeddings_path))
        
        # Create new KB instance and load
        kb2 = KnowledgeBase(knowledge_base_path=self.test_dir)
        self.assertEqual(len(kb2.documents), original_count)
    
    def test_collection_filtering(self):
        """Test collection-based filtering."""
        self.kb.add_text("Doc 1", metadata={"source": "doc1.txt", "collection": "col1"})
        self.kb.add_text("Doc 2", metadata={"source": "doc2.txt", "collection": "col2"})
        
        results = self.kb.search("Doc", n_results=10, collection_name="col1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['metadata']['collection'], 'col1')


if __name__ == '__main__':
    unittest.main()
