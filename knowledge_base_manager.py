import os
import numpy as np
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
        self.metadata_path = os.path.join(knowledge_base_path, "metadata.json")
        self.embeddings_path = os.path.join(knowledge_base_path, "embeddings.npy")
        
        # Initialize embedding model
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Storage for documents, metadata, and embeddings
        self.documents = []
        self.metadatas = []
        self.embeddings = []
        
        # Load existing index if available (check for new JSON/numpy format)
        if os.path.exists(self.metadata_path) and os.path.exists(self.embeddings_path):
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
            
            meta = dict(metadata or {})
            meta['chunk_index'] = i
            self.metadatas.append(meta)
        
        logger.info(f"Added {len(chunks)} chunks to knowledge base")
        self._save_index()
    
    def add_pdf(self, pdf_path: str):
        """Extract text from PDF and add to knowledge base."""
        try:
            filename = os.path.basename(pdf_path).lower()
            
            # Auto-detect document category from filename
            category = None
            if 'emp' in filename:
                category = 'employment'
            elif 'edu' in filename:
                category = 'education'
            elif 'add' in filename or 'address' in filename:
                category = 'address'
            elif 'misc' in filename or 'criminal' in filename:
                category = 'compliance'  # MISC_PM contains red flags, criminal checks, etc.
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                metadata = {"source": os.path.basename(pdf_path), "type": "pdf"}
                if category:
                    metadata['category'] = category
                
                self.add_text(text, metadata=metadata)
                logger.info(f"Added PDF: {pdf_path} (category: {category})")
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
    
    def load_documents_from_folder(self, folder_path: str, collection_name: str = None):
        """Load all supported documents from a folder."""
        supported_extensions = {'.pdf', '.docx', '.txt'}
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            logger.info(f"Created knowledge base folder: {folder_path}")
            return

        # Skip if KB already loaded to avoid re-indexing
        if len(self.documents) > 0:
            logger.info(f"Knowledge base already loaded with {len(self.documents)} documents, skipping re-index of {folder_path}")
            return

        # Determine collection label: explicit parameter takes precedence,
        # otherwise use the folder name if it's a subfolder of the root KB path.
        collection = collection_name
        try:
            abs_root = os.path.abspath(self.knowledge_base_path)
            abs_folder = os.path.abspath(folder_path)
            if collection is None and abs_root != abs_folder:
                collection = os.path.basename(folder_path)
        except Exception:
            collection = collection_name

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            # Skip if it's a directory or our index file
            if os.path.isdir(file_path) or filename == 'embeddings.pkl':
                continue
            
            _, ext = os.path.splitext(filename)
            
            if ext.lower() in supported_extensions:
                # Track how many documents were added before this file
                docs_before = len(self.documents)
                
                if ext == '.pdf':
                    self.add_pdf(file_path)
                elif ext == '.docx':
                    self.add_docx(file_path)
                elif ext == '.txt':
                    self.add_txt(file_path)
                
                # Add collection label to ALL newly added metadata entries
                if collection is not None:
                    docs_added = len(self.documents) - docs_before
                    for i in range(docs_before, len(self.documents)):
                        self.metadatas[i]['collection'] = collection
    
    def search(self, query: str, n_results: int = 3, collection_name: str = None, category: str = None) -> List[Dict]:
        """Search the knowledge base for relevant information using hybrid search.
        
        Args:
            query: Search query string
            n_results: Number of results to return
            collection_name: Filter by collection (e.g., 'springworks')
            category: Filter by document category (e.g., 'employment', 'education', 'address')
        """
        if len(self.documents) == 0:
            return []
        
        # Encode query
        query_embedding = self.embedding_model.encode(query)
        
        # Extract keywords from query for boosting
        query_keywords = set(query.lower().split())
        
        # Calculate cosine similarities
        # If a collection is specified, filter to only those documents
        if collection_name:
            filtered_indices = [i for i, m in enumerate(self.metadatas) if m.get('collection') == collection_name]
            if not filtered_indices:
                return []
            
            # Further filter by category if specified
            if category:
                category_indices = [i for i in filtered_indices if self.metadatas[i].get('category') == category]
                if category_indices:
                    filtered_indices = category_indices
                    logger.info(f"Filtered to {len(filtered_indices)} documents in category '{category}'")
                else:
                    logger.info(f"No documents found in category '{category}'")
                    return []
            
            embeddings_array = np.array([self.embeddings[i] for i in filtered_indices])
            similarities = cosine_similarity([query_embedding], embeddings_array)[0]

            # Apply keyword boosting
            boosted_similarities = []
            for i, sim in enumerate(similarities):
                doc_idx = filtered_indices[i]
                doc_text = self.documents[doc_idx].lower()
                
                # Count keyword matches
                keyword_matches = sum(1 for kw in query_keywords if kw in doc_text)
                
                # Boost score based on keyword matches
                # Each keyword match adds 0.15 to similarity (max boost of 0.7)
                boost = min(keyword_matches * 0.15, 0.7)
                boosted_similarities.append(sim + boost)
            
            boosted_similarities = np.array(boosted_similarities)

            # Get top k results relative to the filtered set
            k = min(n_results, len(filtered_indices))
            top_rel_indices = np.argsort(boosted_similarities)[-k:][::-1]
            top_indices = [filtered_indices[i] for i in top_rel_indices]
            final_similarities = boosted_similarities
        else:
            # No collection filter, but may filter by category
            if category:
                # Filter to only documents in specified category
                filtered_indices = [i for i, m in enumerate(self.metadatas) if m.get('category') == category]
                if not filtered_indices:
                    logger.info(f"No documents found in category '{category}'")
                    return []
            else:
                # No category filter either, use all documents
                filtered_indices = list(range(len(self.documents)))
            
            embeddings_array = np.array([self.embeddings[i] for i in filtered_indices])
            similarities = cosine_similarity([query_embedding], embeddings_array)[0]
            
            # Apply keyword boosting to filtered documents
            boosted_similarities = []
            for i, sim in enumerate(similarities):
                doc_idx = filtered_indices[i]
                doc_text = self.documents[doc_idx].lower()
                
                # Count keyword matches
                keyword_matches = sum(1 for kw in query_keywords if kw in doc_text)
                
                # Boost score based on keyword matches
                boost = min(keyword_matches * 0.1, 0.5)
                boosted_similarities.append(sim + boost)
            
            boosted_similarities = np.array(boosted_similarities)
            
            # Get top k results relative to the filtered set
            k = min(n_results, len(filtered_indices))
            top_rel_indices = np.argsort(boosted_similarities)[-k:][::-1]
            top_indices = [filtered_indices[i] for i in top_rel_indices]
            final_similarities = boosted_similarities
        
        # Format results
        formatted_results = []
        for rank, idx in enumerate(top_indices):
            # Determine similarity value (always use rank since both branches now use filtered_indices)
            try:
                sim_value = float(1 - final_similarities[rank])
            except Exception:
                sim_value = 0.0

            formatted_results.append({
                'content': self.documents[idx],
                'metadata': self.metadatas[idx],
                'distance': sim_value
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
        # Get unique collections
        collections = set(m.get('collection', 'default') for m in self.metadatas)
        return {
            'total_documents': len(self.documents),
            'collections': list(collections),
            'collection_count': len(collections)
        }
    
    def clear(self):
        """Clear all documents from the knowledge base."""
        self.documents = []
        self.metadatas = []
        self.embeddings = []
        self._save_index()
        logger.info("Knowledge base cleared")
    
    def _save_index(self):
        """Save embeddings and metadata to disk using JSON and numpy (safer than pickle)."""
        try:
            os.makedirs(self.knowledge_base_path, exist_ok=True)
            
            # Save metadata as JSON (safe)
            metadata_path = os.path.join(self.knowledge_base_path, "metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                import json
                json.dump({
                    'documents': self.documents,
                    'metadatas': self.metadatas
                }, f, ensure_ascii=False, indent=2)
            
            # Save embeddings as numpy array (safer than pickle)
            embeddings_path = os.path.join(self.knowledge_base_path, "embeddings.npy")
            np.save(embeddings_path, np.array(self.embeddings))
            
            logger.info("Index saved successfully (JSON + numpy)")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def _load_index(self):
        """Load embeddings and metadata from disk (JSON + numpy format)."""
        metadata_path = os.path.join(self.knowledge_base_path, "metadata.json")
        embeddings_path = os.path.join(self.knowledge_base_path, "embeddings.npy")
        
        # Try new format first (JSON + numpy)
        if os.path.exists(metadata_path) and os.path.exists(embeddings_path):
            try:
                import json
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = data['documents']
                    self.metadatas = data['metadatas']
                
                self.embeddings = list(np.load(embeddings_path, allow_pickle=False))
                logger.info(f"Loaded index with {len(self.documents)} documents (JSON + numpy)")
                return
            except Exception as e:
                logger.error(f"Error loading new format index: {e}")
        
        # Fallback to old pickle format (for migration)
        if os.path.exists(self.index_path):
            try:
                import pickle
                with open(self.index_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data['documents']
                    self.metadatas = data['metadatas']
                    self.embeddings = data['embeddings']
                logger.warning(f"Loaded old pickle format. Converting to JSON + numpy...")
                # Immediately save in new format
                self._save_index()
                # Remove old pickle file
                os.remove(self.index_path)
                logger.info("Migration to JSON + numpy complete")
            except Exception as e:
                logger.error(f"Error loading pickle index: {e}")
                self.documents = []
                self.metadatas = []
                self.embeddings = []
        else:
            self.documents = []
            self.metadatas = []
            self.embeddings = []