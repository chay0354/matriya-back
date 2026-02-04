/**
 * LLM Service for generating answers using Together AI or Hugging Face API
 */
import axios from 'axios';
import logger from './logger.js';
import settings from './config.js';

class LLMService {
  /**Service for generating answers using Together AI or Hugging Face API*/
  
  constructor() {
    this.provider = settings.LLM_PROVIDER.toLowerCase();
    
    if (this.provider === "together") {
      this.apiKey = settings.TOGETHER_API_KEY;
      this.model = settings.TOGETHER_MODEL;
      this.apiUrl = "https://api.together.xyz/inference";
    } else {
      // Hugging Face
      this.apiKey = settings.HF_API_TOKEN;
      this.model = settings.HF_MODEL;
      this.apiUrl = `https://api-inference.huggingface.co/models/${this.model}`;
    }
    
    if (!this.apiKey) {
      logger.warn(`${this.provider.toUpperCase()} API key not set. LLM generation will not work.`);
    }
  }

  async generateAnswer(question, context, maxLength = 500) {
    /**
     * Generate an answer based on question and context from RAG
     * 
     * Args:
     *   question: User's question
     *   context: Relevant text chunks from RAG search
     *   max_length: Maximum length of generated answer
     * 
     * Returns:
     *   Generated answer or null if error
     */
    if (!this.apiKey) {
      logger.error(`Cannot generate answer: ${this.provider.toUpperCase()} API key not configured`);
      return null;
    }
    
    // Format prompt for instruction-tuned models
    // Detect language from question and instruct to answer in same language
    const prompt = `Based on the following context, answer the question clearly and concisely. IMPORTANT: Answer in the same language as the question.

Context:
${context}

Question: ${question}

Answer (in the same language as the question):`;
    
    try {
      if (this.provider === "together") {
        // Together AI API format
        const response = await axios.post(
          this.apiUrl,
          {
            model: this.model,
            prompt: prompt,
            max_tokens: maxLength,
            temperature: 0.7,
            top_p: 0.9,
            stop: ["\n\nQuestion:", "Context:", "Answer:"]
          },
          {
            headers: {
              "Authorization": `Bearer ${this.apiKey}`,
              "Content-Type": "application/json"
            },
            timeout: 60000
          }
        );
        
        if (response.status === 200) {
          const result = response.data;
          // Together AI returns: {"output": {"choices": [{"text": "..."}]}}
          let generatedText = "";
          if (result.output && result.output.choices && result.output.choices.length > 0) {
            generatedText = result.output.choices[0].text || "";
          } else if (result.choices && result.choices.length > 0) {
            // Alternative format
            generatedText = result.choices[0].text || "";
          } else {
            // Fallback
            generatedText = result.text || "";
          }
          
          let answer = generatedText.trim();
          
          // Clean up
          if (answer.includes("Answer:")) {
            answer = answer.split("Answer:")[answer.split("Answer:").length - 1].trim();
          }
          
          logger.info(`Generated answer using Together AI (length: ${answer.length})`);
          return answer || null;
        } else {
          const errorMsg = response.data?.error || response.statusText;
          logger.error(`Together AI API error ${response.status}: ${errorMsg}`);
          return null;
        }
      } else {
        // Hugging Face API format
        const response = await axios.post(
          this.apiUrl,
          {
            inputs: prompt,
            parameters: {
              max_new_tokens: maxLength,
              temperature: 0.7,
              top_p: 0.9,
              return_full_text: false
            },
            options: {
              wait_for_model: true
            }
          },
          {
            headers: {
              "Authorization": `Bearer ${this.apiKey}`,
              "Content-Type": "application/json"
            },
            timeout: 60000
          }
        );
        
        if (response.status === 200) {
          const result = response.data;
          let generatedText = "";
          if (Array.isArray(result) && result.length > 0) {
            generatedText = result[0].generated_text || '';
          } else if (typeof result === 'object') {
            generatedText = result.generated_text || '';
          } else {
            generatedText = String(result);
          }
          let answer = generatedText.trim();
          
          if (answer.includes("Answer:")) {
            answer = answer.split("Answer:")[answer.split("Answer:").length - 1].trim();
          }
          
          logger.info(`Generated answer using Hugging Face (length: ${answer.length})`);
          return answer || null;
        } else if (response.status === 503) {
          const errorMsg = response.data?.error || response.statusText;
          logger.warn(`Together AI service unavailable (503): ${errorMsg}`);
          return "המודל AI לא זמין כרגע. אנא נסה שוב בעוד כמה שניות.";
        } else {
          logger.error(`Hugging Face API error ${response.status}: ${response.statusText}`);
          return null;
        }
      }
    } catch (e) {
      if (e.code === 'ECONNABORTED' || e.message.includes('timeout')) {
        logger.error(`${this.provider.toUpperCase()} API request timed out`);
      } else if (e.response) {
        logger.error(`${this.provider.toUpperCase()} API request failed: ${e.response.status} - ${e.response.statusText}`);
      } else {
        logger.error(`${this.provider.toUpperCase()} API request failed: ${e.message}`);
      }
      return null;
    }
  }
  
  isAvailable() {
    /**Check if LLM service is available*/
    return this.apiKey != null && this.apiKey !== "";
  }
}

export default LLMService;
