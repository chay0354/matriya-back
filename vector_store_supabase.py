"""
Supabase vector store using pgvector extension
"""
import os
import logging
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from config import settings
import psycopg2
from psycopg2.extras import execute_values, Json
from psycopg2.pool import SimpleConnectionPool
import hashlib
import json

logger = logging.getLogger(__name__)


class SupabaseVectorStore:
    """Vector store using Supabase PostgreSQL with pgvector"""
    
    def __init__(self, db_url: str, collection_name: str, embedding_model_name: str):
        """
        Initialize Supabase vector store
        
        Args:
            db_url: PostgreSQL connection string
            collection_name: Name of the collection/table
            embedding_model_name: Name of the embedding model
        """
        self.db_url = db_url
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        logger.info(f"Embedding model loaded successfully (dimension: {self.embedding_dim})")
        
        # Create connection pool with timeout
        try:
            self.pool = SimpleConnectionPool(
                1, 10, 
                dsn=db_url,
                connect_timeout=10  # 10 second timeout
            )
            logger.info("Connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
        
        # Initialize collection (table) - non-blocking, will retry on first use if needed
        try:
            self._init_collection()
        except Exception as e:
            logger.warning(f"Collection initialization had issues (may be OK if tables exist): {e}")
            # Don't fail - tables might already exist
    
    def _get_connection(self):
        """Get connection from pool"""
        return self.pool.getconn()
    
    def _return_connection(self, conn):
        """Return connection to pool"""
        self.pool.putconn(conn)
    
    def _init_collection(self):
        """Initialize collection table with pgvector extension"""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Create table if not exists (with dynamic embedding dimension)
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.collection_name} (
                        id TEXT PRIMARY KEY,
                        embedding vector({self.embedding_dim}),
                        document TEXT NOT NULL,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create vector index for similarity search (IMPORTANT for performance)
                # Note: This might take time on first run, but won't block subsequent operations
                try:
                    cur.execute(f"""
                        CREATE INDEX IF NOT EXISTS {self.collection_name}_embedding_idx 
                        ON {self.collection_name} 
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """)
                except Exception as idx_error:
                    # Index creation might fail if table is empty, that's OK
                    logger.warning(f"Index creation warning (may be normal): {idx_error}")
                
                # Create index on metadata for faster filtering
                try:
                    cur.execute(f"""
                        CREATE INDEX IF NOT EXISTS {self.collection_name}_metadata_idx 
                        ON {self.collection_name} 
                        USING GIN (metadata);
                    """)
                except Exception as idx_error:
                    logger.warning(f"Metadata index creation warning: {idx_error}")
                
                # Create index on metadata->filename for file filtering
                try:
                    cur.execute(f"""
                        CREATE INDEX IF NOT EXISTS {self.collection_name}_metadata_filename_idx 
                        ON {self.collection_name} 
                        USING BTREE ((metadata->>'filename'));
                    """)
                except Exception as idx_error:
                    logger.warning(f"Filename index creation warning: {idx_error}")
                
                conn.commit()
                logger.info(f"Collection '{self.collection_name}' initialized")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error initializing collection: {e}")
            # Don't raise - allow the service to continue, table might already exist
            logger.warning("Continuing despite initialization error - table may already exist")
        finally:
            if conn:
                self._return_connection(conn)
    
    def _generate_id(self, text: str, metadata: Dict) -> str:
        """Generate unique ID for document"""
        content = f"{text}_{metadata.get('filename', '')}_{metadata.get('chunk_index', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to vector store
        
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
        )
        
        # Generate IDs if not provided
        if ids is None:
            ids = [self._generate_id(text, meta) for text, meta in zip(texts, metadatas)]
        
        # Insert into database
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Prepare data for bulk insert
                data = []
                for i, (text, meta, embedding, doc_id) in enumerate(zip(texts, metadatas, embeddings, ids)):
                    data.append((
                        doc_id,
                        embedding.tolist(),  # Convert numpy array to list
                        text,
                        Json(meta)  # Convert dict to JSONB using psycopg2's Json adapter
                    ))
                
                # Bulk insert
                execute_values(
                    cur,
                    f"""
                    INSERT INTO {self.collection_name} (id, embedding, document, metadata)
                    VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        document = EXCLUDED.document,
                        metadata = EXCLUDED.metadata
                    """,
                    data,
                    template=None,
                    page_size=100
                )
                
                conn.commit()
                logger.info(f"Added {len(texts)} documents to vector store")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error adding documents: {e}")
            raise
        finally:
            if conn:
                self._return_connection(conn)
        
        return ids
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents using pgvector
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True
        ).tolist()
        
        # Build query
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Build WHERE clause for metadata filtering
                where_clause = ""
                params = []
                
                if filter_metadata:
                    conditions = []
                    for key, value in filter_metadata.items():
                        conditions.append(f"metadata->>'{key}' = %s")
                        params.append(value)
                    where_clause = "WHERE " + " AND ".join(conditions)
                
                # Similarity search using cosine distance
                # Note: query_embedding is used twice in the query
                # psycopg2 should handle Python lists for vector type automatically
                # But we need to ensure it's passed correctly
                query_sql = f"""
                    SELECT 
                        id,
                        document,
                        metadata,
                        1 - (embedding <=> %s::vector) as distance
                    FROM {self.collection_name}
                    {where_clause}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                
                # Build params: [query_embedding, ...filter_values..., query_embedding, n_results]
                # pgvector expects array format as string: '[1,2,3]'
                # Convert Python list to string format that pgvector understands
                embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'
                
                query_params = [embedding_str]
                if filter_metadata:
                    query_params.extend(params)  # Add filter values
                query_params.append(embedding_str)  # Second use for ORDER BY
                query_params.append(n_results)  # LIMIT
                
                logger.debug(f"Query embedding length: {len(query_embedding)}, first few values: {query_embedding[:5] if len(query_embedding) > 5 else query_embedding}")
                
                logger.debug(f"Executing query with {len(query_params)} parameters")
                logger.debug(f"Query SQL: {query_sql[:200]}...")
                
                # First, check if table has any rows
                cur.execute(f"SELECT COUNT(*) FROM {self.collection_name}")
                total_count = cur.fetchone()[0]
                logger.info(f"Total documents in table: {total_count}")
                
                if total_count == 0:
                    logger.warning("No documents in table, returning empty results")
                    return []
                
                # Execute the search query
                cur.execute(query_sql, query_params)
                results = cur.fetchall()
                logger.info(f"Query returned {len(results)} results")
                
                # If no results, try a simpler query to debug
                if len(results) == 0:
                    logger.warning("No results from vector search, trying debug query...")
                    cur.execute(f"SELECT id, LEFT(document::text, 50) FROM {self.collection_name} LIMIT 1")
                    debug_row = cur.fetchone()
                    if debug_row:
                        logger.info(f"Sample document exists: {debug_row[0][:50]}...")
                    else:
                        logger.error("No documents found even in simple query!")
                
                # Format results
                formatted_results = []
                for row in results:
                    if len(row) < 4:
                        logger.warning(f"Unexpected row format: {row}")
                        continue
                    
                    # Handle metadata - it might be dict or already JSON
                    metadata = row[2]
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    elif not isinstance(metadata, dict):
                        metadata = {}
                    
                    formatted_results.append({
                        'id': row[0],
                        'document': row[1],
                        'metadata': metadata,
                        'distance': float(row[3]) if len(row) > 3 and row[3] is not None else None
                    })
                
                return formatted_results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise
        finally:
            if conn:
                self._return_connection(conn)
    
    def get_all_filenames(self) -> List[str]:
        """Get list of all unique filenames in the collection"""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT DISTINCT metadata->>'filename' as filename
                    FROM {self.collection_name}
                    WHERE metadata->>'filename' IS NOT NULL
                    ORDER BY filename
                """)
                results = cur.fetchall()
                return [row[0] for row in results if row[0]]
        except Exception as e:
            logger.error(f"Error getting filenames: {e}")
            return []
        finally:
            if conn:
                self._return_connection(conn)
    
    def get_collection_info(self) -> Dict:
        """Get information about the collection"""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {self.collection_name}")
                count = cur.fetchone()[0]
                
                return {
                    'collection_name': self.collection_name,
                    'document_count': count,
                    'db_path': 'Supabase PostgreSQL'
                }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                'collection_name': self.collection_name,
                'document_count': 0,
                'db_path': 'Supabase PostgreSQL'
            }
        finally:
            if conn:
                self._return_connection(conn)
    
    def delete_documents(self, ids: Optional[List[str]] = None, filter_metadata: Optional[Dict] = None) -> Dict:
        """
        Delete documents by IDs or filter metadata
        
        Args:
            ids: List of document IDs to delete
            filter_metadata: Metadata filter to delete matching documents
            
        Returns:
            Dictionary with deletion results
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                if ids:
                    # Delete by IDs
                    placeholders = ','.join(['%s'] * len(ids))
                    cur.execute(
                        f"DELETE FROM {self.collection_name} WHERE id IN ({placeholders})",
                        ids
                    )
                    deleted_count = cur.rowcount
                elif filter_metadata:
                    # Delete by metadata filter
                    conditions = []
                    params = []
                    for key, value in filter_metadata.items():
                        conditions.append(f"metadata->>'{key}' = %s")
                        params.append(value)
                    where_clause = "WHERE " + " AND ".join(conditions)
                    
                    cur.execute(
                        f"DELETE FROM {self.collection_name} {where_clause}",
                        params
                    )
                    deleted_count = cur.rowcount
                else:
                    return {"deleted_count": 0, "error": "Either ids or filter_metadata must be provided"}
                
                conn.commit()
                logger.info(f"Deleted {deleted_count} documents")
                return {"deleted_count": deleted_count}
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error deleting documents: {e}")
            return {"deleted_count": 0, "error": str(e)}
        finally:
            if conn:
                self._return_connection(conn)
    
    def reset_collection(self) -> bool:
        """Reset the collection (delete all documents)"""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE TABLE {self.collection_name}")
                conn.commit()
                logger.info("Collection reset successfully")
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error resetting collection: {e}")
            return False
        finally:
            if conn:
                self._return_connection(conn)
