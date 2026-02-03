"""
Vector database management using ChromaDB
"""
import os
# Disable telemetry before importing chromadb
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY_DISABLED'] = 'True'

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
import hashlib

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector database operations using ChromaDB"""
    
    def __init__(self, db_path: str, collection_name: str, embedding_model_name: str):
        """
        Initialize vector store
        
        Args:
            db_path: Path to ChromaDB database
            collection_name: Name of the collection
            embedding_model_name: Name of the embedding model
        """
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name
        
        # Initialize ChromaDB client (persistent, local)
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model (local)
        logger.info(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        logger.info("Embedding model loaded successfully")
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """Get existing collection or create a new one"""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Document embeddings for RAG system"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
        return collection
    
    def _generate_id(self, text: str, metadata: Dict) -> str:
        """Generate a unique ID for a document chunk"""
        content = f"{text}{metadata.get('filename', '')}{metadata.get('chunk_index', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the vector store
        
        Args:
            texts: List of text chunks
            metadatas: List of metadata dictionaries
            ids: Optional list of IDs (will be generated if not provided)
            
        Returns:
            List of document IDs
        """
        if not texts:
            return []
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        ).tolist()
        
        # Generate IDs if not provided
        if ids is None:
            ids = [self._generate_id(text, meta) for text, meta in zip(texts, metadatas)]
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(texts)} documents to vector store")
        return ids
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents with improved retrieval
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of search results with documents, metadata, and distances
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True,
            show_progress_bar=False
        ).tolist()
        
        # Search in collection - get more results for better ranking
        where = filter_metadata if filter_metadata else None
        
        # Request more results than needed for better ranking
        search_n = max(n_results * 2, 10)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=search_n,
            where=where
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results and results['distances'] else None,
                    'id': results['ids'][0][i] if 'ids' in results else None
                })
        
        return formatted_results
    
    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents by IDs"""
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            return False
    
    def get_collection_info(self) -> Dict:
        """Get information about the collection"""
        count = self.collection.count()
        return {
            'collection_name': self.collection_name,
            'document_count': count,
            'db_path': str(self.db_path)
        }
    
    def get_all_filenames(self) -> List[str]:
        """Get list of all unique filenames in the collection"""
        try:
            # Get all documents from collection
            results = self.collection.get()
            
            if not results or not results.get('metadatas'):
                return []
            
            # Extract unique filenames
            filenames = set()
            for metadata in results['metadatas']:
                if metadata and 'filename' in metadata:
                    filenames.add(metadata['filename'])
            
            return sorted(list(filenames))
        except Exception as e:
            logger.error(f"Error getting filenames: {str(e)}")
            return []
    
    def reset_collection(self):
        """Reset the collection (delete all documents)"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self._get_or_create_collection()
            logger.info("Collection reset successfully")
            return True
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            return False
