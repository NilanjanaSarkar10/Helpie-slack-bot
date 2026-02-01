import os
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
from docx import Document
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeBase:
    """Manages document storage, embedding, and retrieval for the Slack bot."""
    
    def __init__(self, knowledge_base_path: str = "./knowledge_base"):
        self.knowledge_base_path = knowledge_base_path
        self.index_path = os.path.join(knowledge_base_path, "embeddings.pkl")
        
        # Initialize embedding model
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Storage for documents, metadata, and embeddings
        self.documents = []
        self.metadatas = []
        self.embeddings = []
        
        # Load existing index if available
        if os.path.exists(self.index_path):
            self._load_index()
        else:
            logger.info("Created new knowledge base")
    
    def add_text(self, text: str, metadata: Dict = None):
        """Add a text document to the knowledge base."""
        if not text.strip():
            return
        
        # Create chunks of text
        chunks = self._chunk_text(text)
        
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = self.embedding_model.encode(chunk)
            
            # Store document, metadata, and embedding
            self.documents.append(chunk)
            self.embeddings.append(embedding)
            
            meta = metadata or {}
            meta['chunk_index'] = i
            self.metadatas.append(meta)
        
        logger.info(f"Added {len(chunks)} chunks to knowledge base")
        self._save_index()
    
    def add_pdf(self, pdf_path: str):
        """Extract text from PDF and add to knowledge base."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                self.add_text(
                    text,
                    metadata={"source": os.path.basename(pdf_path), "type": "pdf"}
                )
                logger.info(f"Added PDF: {pdf_path}")
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
    
    def add_docx(self, docx_path: str):
        """Extract text from DOCX and add to knowledge base."""
        try:
            doc = Document(docx_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            self.add_text(
                text,
                metadata={"source": os.path.basename(docx_path), "type": "docx"}
            )
            logger.info(f"Added DOCX: {docx_path}")
        except Exception as e:
            logger.error(f"Error processing DOCX {docx_path}: {e}")
    
    def add_txt(self, txt_path: str):
        """Read text file and add to knowledge base."""
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                text = file.read()
                
                self.add_text(
                    text,
                    metadata={"source": os.path.basename(txt_path), "type": "txt"}
                )
                logger.info(f"Added TXT: {txt_path}")
        except Exception as e:
            logger.error(f"Error processing TXT {txt_path}: {e}")
    
    def load_documents_from_folder(self, folder_path: str):
        """Load all supported documents from a folder."""
        supported_extensions = {'.pdf', '.docx', '.txt'}
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            logger.info(f"Created knowledge base folder: {folder_path}")
            return
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            # Skip if it's a directory or our index file
            if os.path.isdir(file_path) or filename == 'embeddings.pkl':
                continue
            
            _, ext = os.path.splitext(filename)
            
            if ext.lower() in supported_extensions:
                if ext == '.pdf':
                    self.add_pdf(file_path)
                elif ext == '.docx':
                    self.add_docx(file_path)
                elif ext == '.txt':
                    self.add_txt(file_path)
    
    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search the knowledge base for relevant information."""
        if len(self.documents) == 0:
            return []
        
        # Encode query
        query_embedding = self.embedding_model.encode(query)
        
        # Calculate cosine similarities
        embeddings_array = np.array(self.embeddings)
        similarities = cosine_similarity([query_embedding], embeddings_array)[0]
        
        # Get top k results
        k = min(n_results, len(self.documents))
        top_indices = np.argsort(similarities)[-k:][::-1]
        
        # Format results
        formatted_results = []
        for idx in top_indices:
            formatted_results.append({
                'content': self.documents[idx],
                'metadata': self.metadatas[idx],
                'distance': float(1 - similarities[idx])
            })
        
        return formatted_results
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into chunks with overlap."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks if chunks else [text]
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics."""
        return {
            'total_documents': len(self.documents),
            'collection_name': 'sklearn_index'
        }
    
    def clear(self):
        """Clear all documents from the knowledge base."""
        self.documents = []
        self.metadatas = []
        self.embeddings = []
        self._save_index()
        logger.info("Knowledge base cleared")
    
    def _save_index(self):
        """Save embeddings and metadata to disk."""
        try:
            os.makedirs(self.knowledge_base_path, exist_ok=True)
            with open(self.index_path, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'metadatas': self.metadatas,
                    'embeddings': self.embeddings
                }, f)
            logger.info("Index saved successfully")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def _load_index(self):
        """Load embeddings and metadata from disk."""
        try:
            with open(self.index_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.metadatas = data['metadatas']
                self.embeddings = data['embeddings']
            logger.info(f"Loaded existing index with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            self.documents = []
            self.metadatas = []
            self.embeddings = []
