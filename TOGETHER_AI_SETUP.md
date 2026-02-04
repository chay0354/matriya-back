# Together AI Setup Guide

## What is Together AI?

Together AI provides API access to various open-source LLM models, including:
- Mistral 7B
- Llama 2/3
- Qwen
- And many more

## Setup Steps

### 1. Get Together AI API Key

1. Go to: https://together.ai/
2. Sign up for an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the API key

### 2. Update `.env` File

Edit `back/.env` and add your Together AI API key:

```env
LLM_PROVIDER=together
TOGETHER_API_KEY=your_actual_api_key_here
TOGETHER_MODEL=mistralai/Mistral-7B-Instruct-v0.2
```

### 3. Available Models

Together AI supports many models. Good options for Hebrew:

- `mistralai/Mistral-7B-Instruct-v0.2` (Recommended - excellent Hebrew)
- `meta-llama/Llama-2-7b-chat-hf` (Good multilingual)
- `Qwen/Qwen2-7B-Instruct` (Excellent multilingual)
- `mistralai/Mixtral-8x7B-Instruct-v0.1` (Larger, better quality)

### 4. Pricing

Together AI has pay-as-you-go pricing. Check their website for current rates.

### 5. Test the Integration

After adding your API key, restart the backend and test:

```bash
cd E:\mat
python test_ai_answer.py
```

## Benefits of Together AI

✅ **Reliable API** - No endpoint deprecation issues
✅ **Many Models** - Access to various open-source models
✅ **Good Hebrew Support** - Models like Mistral work well with Hebrew
✅ **Fast** - Optimized inference infrastructure
✅ **Simple** - Easy API integration

## Switching Back to Hugging Face

If you want to use Hugging Face instead:

```env
LLM_PROVIDER=huggingface
HF_API_TOKEN=your_hf_token
HF_MODEL=microsoft/phi-2
```
