/**
 * Text chunking utilities for RAG system
 */
class TextChunker {
  /**
   * Splits documents into chunks for embedding
   * 
   * Args:
   *   chunk_size: Maximum size of each chunk (in characters)
   *   chunk_overlap: Number of characters to overlap between chunks
   */
  constructor(chunkSize = 1000, chunkOverlap = 200) {
    this.chunkSize = chunkSize;
    this.chunkOverlap = chunkOverlap;
  }

  chunkText(text, metadata, chunkSize = null, chunkOverlap = null) {
    /**
     * Split text into chunks
     * 
     * Args:
     *   text: Text to chunk
     *   metadata: Base metadata for all chunks
     *   chunk_size: Override default chunk size
     *   chunk_overlap: Override default chunk overlap
     * 
     * Returns:
     *   List of chunk dictionaries with 'text' and 'metadata'
     */
    if (!text || !text.trim()) {
      return [];
    }

    const size = chunkSize || this.chunkSize;
    const overlap = chunkOverlap || this.chunkOverlap;

    // Clean and normalize text
    const cleanedText = this._cleanText(text);

    // Split by paragraphs first (better semantic boundaries)
    const paragraphs = this._splitIntoParagraphs(cleanedText);

    const chunks = [];
    let currentChunk = "";
    let chunkIndex = 0;

    for (const paragraph of paragraphs) {
      // If adding this paragraph would exceed chunk size
      if (currentChunk.length + paragraph.length + 1 > size && currentChunk) {
        // Save current chunk
        chunks.push({
          text: currentChunk.trim(),
          metadata: {
            ...metadata,
            chunk_index: chunkIndex,
            chunk_size: currentChunk.length
          }
        });
        chunkIndex++;

        // Start new chunk with overlap
        if (overlap > 0 && currentChunk.length > overlap) {
          const overlapText = currentChunk.slice(-overlap);
          currentChunk = overlapText + "\n" + paragraph;
        } else {
          currentChunk = paragraph;
        }
      } else {
        // Add paragraph to current chunk
        if (currentChunk) {
          currentChunk += "\n" + paragraph;
        } else {
          currentChunk = paragraph;
        }
      }
    }

    // Add final chunk
    if (currentChunk.trim()) {
      chunks.push({
        text: currentChunk.trim(),
        metadata: {
          ...metadata,
          chunk_index: chunkIndex,
          chunk_size: currentChunk.length
        }
      });
    }

    // If text is shorter than chunk_size, ensure we have at least one chunk
    if (chunks.length === 0 && text) {
      chunks.push({
        text: text,
        metadata: {
          ...metadata,
          chunk_index: 0,
          chunk_size: text.length
        }
      });
    }

    return chunks;
  }

  _cleanText(text) {
    /**Clean and normalize text*/
    // Remove excessive whitespace
    let cleaned = text.replace(/\s+/g, ' ');
    // Remove excessive newlines
    cleaned = cleaned.replace(/\n{3,}/g, '\n\n');
    return cleaned.trim();
  }

  _splitIntoParagraphs(text) {
    /**Split text into paragraphs and sentences*/
    // First split by double newlines (paragraphs)
    const paragraphs = text.split(/\n\s*\n/);

    const result = [];
    for (const para of paragraphs) {
      const trimmed = para.trim();
      if (!trimmed) {
        continue;
      }

      // If paragraph is longer than chunk_size, split by sentences
      if (trimmed.length > this.chunkSize) {
        // Split by sentence endings (Hebrew and English)
        const sentences = trimmed.split(/([.!?]\s+)/);
        // Recombine sentences with their punctuation
        let currentSentence = "";
        for (let i = 0; i < sentences.length; i += 2) {
          if (i < sentences.length) {
            let sentence = sentences[i];
            if (i + 1 < sentences.length) {
              sentence += sentences[i + 1];
            }
            currentSentence += sentence;

            // If accumulated sentences are long enough, add as paragraph
            if (currentSentence.length > this.chunkSize / 2) {
              result.push(currentSentence.trim());
              currentSentence = "";
            }
          }
        }

        if (currentSentence.trim()) {
          result.push(currentSentence.trim());
        }
      } else {
        result.push(trimmed);
      }
    }

    return result;
  }
}

export default TextChunker;
