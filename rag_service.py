"""
Main RAG service that orchestrates document processing, chunking, and vector storage
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional
from document_processor import DocumentProcessor
from chunker import TextChunker
from config import settings

# Import vector store based on mode
if settings.DB_MODE.lower() == "supabase":
    from vector_store_supabase import SupabaseVectorStore as VectorStore
else:
    from vector_store import VectorStore

from llm_service import LLMService

logger = logging.getLogger(__name__)


class RAGService:
    """Main service for RAG operations"""
    
    def __init__(self):
        """Initialize RAG service components"""
        self.document_processor = DocumentProcessor()
        self.chunker = TextChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        # Initialize vector store based on mode
        if settings.DB_MODE.lower() == "supabase":
            if not settings.SUPABASE_DB_URL:
                raise ValueError("SUPABASE_DB_URL must be set when DB_MODE=supabase")
            self.vector_store = VectorStore(
                db_url=settings.SUPABASE_DB_URL,
                collection_name=settings.COLLECTION_NAME,
                embedding_model_name=settings.EMBEDDING_MODEL
            )
        else:
            # Local ChromaDB
            self.vector_store = VectorStore(
                db_path=settings.CHROMA_DB_PATH,
                collection_name=settings.COLLECTION_NAME,
                embedding_model_name=settings.EMBEDDING_MODEL
            )
        self.llm_service = LLMService()
    
    def ingest_file(self, file_path: str) -> Dict:
        """
        Process a file and add it to the vector database
        
        Args:
            file_path: Path to the file to ingest
            
        Returns:
            Dictionary with ingestion results
        """
        logger.info(f"Starting ingestion for file: {file_path}")
        
        # Process document
        result = self.document_processor.process_file(file_path)
        
        if not result['success']:
            return {
                'success': False,
                'error': result['error'],
                'file_path': file_path
            }
        
        text = result['text']
        metadata = result['metadata']
        
        if not text or not text.strip():
            return {
                'success': False,
                'error': 'No text extracted from file',
                'file_path': file_path
            }
        
        # Chunk the text
        logger.info(f"Chunking document into pieces...")
        chunks = self.chunker.chunk_text(text, metadata)
        logger.info(f"Created {len(chunks)} chunks")
        
        if not chunks:
            return {
                'success': False,
                'error': 'Failed to create chunks from document',
                'file_path': file_path
            }
        
        # Extract texts and metadatas for vector store
        texts = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        # Add to vector store
        try:
            ids = self.vector_store.add_documents(texts, metadatas)
            logger.info(f"Successfully ingested file: {file_path}")
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': metadata['filename'],
                'chunks_count': len(chunks),
                'document_ids': ids,
                'metadata': metadata
            }
        except Exception as e:
            logger.error(f"Error adding to vector store: {str(e)}")
            return {
                'success': False,
                'error': f'Error adding to vector store: {str(e)}',
                'file_path': file_path
            }
    
    def ingest_directory(self, directory_path: str) -> Dict:
        """
        Process all supported files in a directory
        
        Args:
            directory_path: Path to directory containing files
            
        Returns:
            Dictionary with ingestion results for all files
        """
        directory = Path(directory_path)
        if not directory.exists():
            return {
                'success': False,
                'error': f'Directory not found: {directory_path}'
            }
        
        results = {
            'success': True,
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'files': []
        }
        
        # Find all supported files
        supported_extensions = set(settings.ALLOWED_EXTENSIONS)
        files = [
            f for f in directory.rglob('*')
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
        
        results['total_files'] = len(files)
        
        for file_path in files:
            result = self.ingest_file(str(file_path))
            results['files'].append(result)
            
            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
        
        results['success'] = results['failed'] == 0
        
        return results
    
    def search(self, query: str, n_results: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Search for relevant documents with improved ranking
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of search results, sorted by relevance
        """
        # Search with more results initially, then re-rank
        initial_results = self.vector_store.search(query, n_results * 3, filter_metadata)
        
        if not initial_results:
            return []
        
        # Re-rank results based on multiple factors
        scored_results = []
        query_lower = query.lower()
        query_words = set([w.strip() for w in query_lower.split() if len(w.strip()) > 1])
        
        # Extract key terms from query (remove common Hebrew question words)
        question_words = {'מה', 'מי', 'איפה', 'מתי', 'איך', 'למה', 'של', 'את', 'ה', 'הוא', 'היא', 'הם', 'הן'}
        key_terms = [w for w in query_words if w not in question_words]
        
        for result in initial_results:
            score = 0.0
            document = result.get('document', '')
            document_lower = document.lower()
            distance = result.get('distance', 999) if result.get('distance') is not None else 999
            
            # Factor 1: Inverse distance (closer = better)
            # Normalize distance to 0-1 scale (assuming max distance ~2.0)
            if distance < 999:
                distance_score = max(0, 1 - (distance / 2.0))
                score += distance_score * 0.4  # 40% weight on semantic similarity
            
            # Factor 2: Keyword matching (exact word matches) - improved for Hebrew
            doc_words = set([w.strip() for w in document_lower.split() if len(w.strip()) > 1])
            word_matches = len(query_words.intersection(doc_words))
            if len(query_words) > 0:
                keyword_score = word_matches / len(query_words)
                score += keyword_score * 0.5  # 50% weight on keyword matching (increased)
            
            # Factor 2b: Partial word matches (for Hebrew morphology)
            partial_matches = 0
            for q_word in query_words:
                if any(q_word in doc_word or doc_word in q_word for doc_word in doc_words):
                    partial_matches += 1
            if len(query_words) > 0:
                partial_score = partial_matches / len(query_words) * 0.2
                score += partial_score
            
            # Factor 3: Key term matching (important words from query)
            if key_terms:
                key_term_matches = sum(1 for term in key_terms if term in document_lower)
                key_term_score = key_term_matches / len(key_terms)
                score += key_term_score * 0.15  # 15% weight on key terms
            
            # Factor 4: Query substring in document (exact phrase)
            if query_lower in document_lower:
                score += 0.05  # 5% bonus for exact phrase match
            
            # Factor 5: Numbers and specific values (important for financial queries)
            import re
            query_numbers = re.findall(r'\d+[.,]?\d*', query)
            if query_numbers:
                doc_numbers = re.findall(r'\d+[.,]?\d*', document)
                number_matches = len(set(query_numbers).intersection(set(doc_numbers)))
                if number_matches > 0:
                    score += 0.1  # 10% bonus for number matches
            
            scored_results.append({
                **result,
                'relevance_score': score
            })
        
        # Sort by relevance score (highest first)
        scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top n_results
        return scored_results[:n_results]
    
    def generate_answer(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None,
        use_llm: bool = True
    ) -> Dict:
        """
        Search for relevant documents and generate an answer using LLM
        
        Args:
            query: User's question
            n_results: Number of RAG results to use as context
            filter_metadata: Optional metadata filters
            use_llm: Whether to use LLM to generate answer (default: True)
            
        Returns:
            Dictionary with search results and generated answer
        """
        try:
            # First, search for relevant chunks
            search_results = self.search(query, n_results, filter_metadata)
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return {
                'query': query,
                'results': [],
                'results_count': 0,
                'answer': None,
                'context_used': 0,
                'error': f'Search error: {str(e)}'
            }
        
        if not search_results:
            return {
                'query': query,
                'results': [],
                'results_count': 0,
                'answer': None,
                'context_used': 0,
                'error': 'No relevant documents found'
            }
        
        # Combine top results into context
        context_parts = []
        for i, result in enumerate(search_results[:n_results], 1):
            doc_text = result.get('document', '')
            filename = result.get('metadata', {}).get('filename', 'Unknown')
            context_parts.append(f"[Source {i} from {filename}]:\n{doc_text}\n")
        
        context = "\n".join(context_parts)
        
        # Generate answer using LLM if available
        answer = None
        if use_llm and self.llm_service.is_available():
            logger.info("Generating answer using LLM...")
            answer = self.llm_service.generate_answer(query, context)
        elif use_llm:
            logger.warning("LLM service not available, returning search results only")
        
        return {
            'query': query,
            'results': search_results,
            'results_count': len(search_results),
            'answer': answer,
            'context_used': len(context_parts),
            'context': context  # Include context for agent analysis
        }
    
    def get_collection_info(self) -> Dict:
        """Get information about the vector database collection"""
        return self.vector_store.get_collection_info()
    
    def check_contradictions(
        self,
        answer: str,
        context: str,
        query: str
    ) -> Dict:
        """
        Contradiction Agent - Checks for contradictions in the answer
        
        Args:
            answer: The answer from Doc Agent
            context: The context used to generate the answer
            query: Original user query
            
        Returns:
            Dictionary with contradiction analysis
        """
        if not answer or not context:
            return {
                'has_contradictions': False,
                'analysis': 'לא ניתן לבדוק סתירות ללא תשובה או הקשר',
                'contradictions': []
            }
        
        # Build prompt for contradiction detection
        prompt = f"""אתה סוכן בדיקת סתירות. בדוק את התשובה הבאה מול ההקשר שסופק וזהה סתירות, אי-התאמות או מידע סותר.

השאלה המקורית: {query}

ההקשר מהמסמכים:
{context}

התשובה שניתנה:
{answer}

בדוק את התשובה בקפידה:
1. האם יש סתירות בין התשובה לבין ההקשר?
2. האם התשובה מכילה מידע שלא מופיע בהקשר?
3. האם יש אי-התאמות או מידע סותר?

השב בעברית:
- אם יש סתירות: ציין אותן בפירוט
- אם אין סתירות: אמת שהתשובה תואמת להקשר

תשובה:"""
        
        try:
            analysis = self.llm_service.generate_answer(
                "בדוק סתירות",
                prompt,
                max_length=800
            )
            
            if not analysis:
                return {
                    'has_contradictions': None,
                    'analysis': 'שגיאה בבדיקת סתירות',
                    'contradictions': []
                }
            
            # Simple heuristic: check if analysis mentions contradictions
            has_contradictions = any(word in analysis.lower() for word in [
                'סתירה', 'סותר', 'אי-התאמה', 'לא תואם', 'שגוי', 'לא נכון'
            ])
            
            return {
                'has_contradictions': has_contradictions,
                'analysis': analysis,
                'contradictions': []  # Could be enhanced to extract specific contradictions
            }
        except Exception as e:
            logger.error(f"Error checking contradictions: {e}")
            return {
                'has_contradictions': None,
                'analysis': f'שגיאה בבדיקת סתירות: {str(e)}',
                'contradictions': []
            }
    
    def check_risks(
        self,
        answer: str,
        context: str,
        query: str
    ) -> Dict:
        """
        Risk Agent - Identifies risks in the answer
        
        Args:
            answer: The answer from Doc Agent
            context: The context used to generate the answer
            query: Original user query
            
        Returns:
            Dictionary with risk analysis
        """
        if not answer or not context:
            return {
                'has_risks': False,
                'analysis': 'לא ניתן לזהות סיכונים ללא תשובה או הקשר',
                'risks': []
            }
        
        # Build prompt for risk detection
        prompt = f"""אתה סוכן זיהוי סיכונים. בדוק את התשובה הבאה וזהה סיכונים פוטנציאליים, בעיות, או אזהרות.

השאלה המקורית: {query}

ההקשר מהמסמכים:
{context}

התשובה שניתנה:
{answer}

בדוק את התשובה בקפידה וזהה:
1. סיכונים משפטיים או פיננסיים
2. סיכונים תפעוליים או ביצועיים
3. אזהרות או תנאים חשובים
4. מידע חסר שעלול להוות סיכון
5. אי-בהירות שעלולה לגרום לבעיות

השב בעברית:
- אם יש סיכונים: ציין אותם בפירוט והסבר את החשיבות
- אם אין סיכונים משמעותיים: אמת שהתשובה בטוחה

תשובה:"""
        
        try:
            analysis = self.llm_service.generate_answer(
                "זהה סיכונים",
                prompt,
                max_length=800
            )
            
            if not analysis:
                return {
                    'has_risks': None,
                    'analysis': 'שגיאה בזיהוי סיכונים',
                    'risks': []
                }
            
            # Simple heuristic: check if analysis mentions risks
            has_risks = any(word in analysis.lower() for word in [
                'סיכון', 'אזהרה', 'בעיה', 'חסר', 'לא ברור', 'תשומת לב', 'זהירות'
            ])
            
            return {
                'has_risks': has_risks,
                'analysis': analysis,
                'risks': []  # Could be enhanced to extract specific risks
            }
        except Exception as e:
            logger.error(f"Error checking risks: {e}")
            return {
                'has_risks': None,
                'analysis': f'שגיאה בזיהוי סיכונים: {str(e)}',
                'risks': []
            }
    
    def get_all_filenames(self) -> List[str]:
        """Get list of all unique filenames in the collection"""
        return self.vector_store.get_all_filenames()
    
    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents by IDs"""
        return self.vector_store.delete_documents(ids)
    
    def reset_database(self) -> bool:
        """Reset the entire vector database"""
        return self.vector_store.reset_collection()
