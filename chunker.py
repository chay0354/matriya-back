"""
Text chunking utilities for RAG system
"""
from typing import List, Dict, Optional
import re


class TextChunker:
    """Splits documents into chunks for embedding"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize chunker
        
        Args:
            chunk_size: Maximum size of each chunk (in characters)
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(
        self,
        text: str,
        metadata: Dict,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[Dict]:
        """
        Split text into chunks
        
        Args:
            text: Text to chunk
            metadata: Base metadata for all chunks
            chunk_size: Override default chunk size
            chunk_overlap: Override default chunk overlap
            
        Returns:
            List of chunk dictionaries with 'text' and 'metadata'
        """
        if not text or not text.strip():
            return []
        
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Split by paragraphs first (better semantic boundaries)
        paragraphs = self._split_into_paragraphs(text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) + 1 > chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'text': current_chunk.strip(),
                    'metadata': {
                        **metadata,
                        'chunk_index': chunk_index,
                        'chunk_size': len(current_chunk)
                    }
                })
                chunk_index += 1
                
                # Start new chunk with overlap
                if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                    overlap_text = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_text + "\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'metadata': {
                    **metadata,
                    'chunk_index': chunk_index,
                    'chunk_size': len(current_chunk)
                }
            })
        
        # If text is shorter than chunk_size, ensure we have at least one chunk
        if not chunks and text:
            chunks.append({
                'text': text,
                'metadata': {
                    **metadata,
                    'chunk_index': 0,
                    'chunk_size': len(text)
                }
            })
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs and sentences"""
        # First split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # If paragraphs are too long, split by sentences
        result = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If paragraph is longer than chunk_size, split by sentences
            if len(para) > self.chunk_size:
                # Split by sentence endings (Hebrew and English)
                sentences = re.split(r'([.!?]\s+)', para)
                # Recombine sentences with their punctuation
                current_sentence = ""
                for i in range(0, len(sentences), 2):
                    if i < len(sentences):
                        sentence = sentences[i]
                        if i + 1 < len(sentences):
                            sentence += sentences[i + 1]
                        current_sentence += sentence
                        
                        # If accumulated sentences are long enough, add as paragraph
                        if len(current_sentence) > self.chunk_size // 2:
                            result.append(current_sentence.strip())
                            current_sentence = ""
                
                if current_sentence.strip():
                    result.append(current_sentence.strip())
            else:
                result.append(para)
        
        return result
