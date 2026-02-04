"""
LLM Service for generating answers using Together AI or Hugging Face API
"""
import logging
import requests
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating answers using Together AI or Hugging Face API"""
    
    def __init__(self):
        """Initialize LLM service"""
        self.provider = settings.LLM_PROVIDER.lower()
        
        if self.provider == "together":
            self.api_key = settings.TOGETHER_API_KEY
            self.model = settings.TOGETHER_MODEL
            self.api_url = "https://api.together.xyz/inference"
        else:
            # Hugging Face
            self.api_key = settings.HF_API_TOKEN
            self.model = settings.HF_MODEL
            self.api_url = f"https://api-inference.huggingface.co/models/{self.model}"
        
        if not self.api_key:
            logger.warning(f"{self.provider.upper()} API key not set. LLM generation will not work.")
    
    def generate_answer(
        self,
        question: str,
        context: str,
        max_length: int = 500
    ) -> Optional[str]:
        """
        Generate an answer based on question and context from RAG
        
        Args:
            question: User's question
            context: Relevant text chunks from RAG search
            max_length: Maximum length of generated answer
            
        Returns:
            Generated answer or None if error
        """
        if not self.api_key:
            logger.error(f"Cannot generate answer: {self.provider.upper()} API key not configured")
            return None
        
        # Format prompt for instruction-tuned models
        # Detect language from question and instruct to answer in same language
        prompt = f"""Based on the following context, answer the question clearly and concisely. IMPORTANT: Answer in the same language as the question.

Context:
{context}

Question: {question}

Answer (in the same language as the question):"""
        
        try:
            if self.provider == "together":
                # Together AI API format
                response = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "max_tokens": max_length,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "stop": ["\n\nQuestion:", "Context:", "Answer:"]
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Together AI returns: {"output": {"choices": [{"text": "..."}]}}
                    if "output" in result and "choices" in result["output"]:
                        if len(result["output"]["choices"]) > 0:
                            generated_text = result["output"]["choices"][0].get("text", "")
                        else:
                            generated_text = ""
                    elif "choices" in result:
                        # Alternative format
                        if len(result["choices"]) > 0:
                            generated_text = result["choices"][0].get("text", "")
                        else:
                            generated_text = ""
                    else:
                        # Fallback
                        generated_text = str(result).get("text", "")
                    
                    answer = generated_text.strip()
                    
                    # Clean up
                    if "Answer:" in answer:
                        answer = answer.split("Answer:")[-1].strip()
                    
                    logger.info(f"Generated answer using Together AI (length: {len(answer)})")
                    return answer if answer else None
                else:
                    error_msg = response.text
                    logger.error(f"Together AI API error {response.status_code}: {error_msg}")
                    return None
            else:
                # Hugging Face API format
                response = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": max_length,
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "return_full_text": False
                        },
                        "options": {
                            "wait_for_model": True
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get('generated_text', '')
                    elif isinstance(result, dict):
                        generated_text = result.get('generated_text', '')
                    else:
                        generated_text = str(result)
                    answer = generated_text.strip()
                    
                    if "Answer:" in answer:
                        answer = answer.split("Answer:")[-1].strip()
                    
                    logger.info(f"Generated answer using Hugging Face (length: {len(answer)})")
                    return answer if answer else None
                elif response.status_code == 503:
                    error_msg = response.text
                    logger.warning(f"Together AI service unavailable (503): {error_msg}")
                    return "המודל AI לא זמין כרגע. אנא נסה שוב בעוד כמה שניות."
                else:
                    logger.error(f"Hugging Face API error {response.status_code}: {response.text}")
                    return None
                
        except requests.exceptions.Timeout:
            logger.error(f"{self.provider.upper()} API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.provider.upper()} API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating answer: {str(e)}")
            return None
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.api_key is not None and self.api_key != ""
