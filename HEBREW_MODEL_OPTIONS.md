# Hebrew Language Support for LLM Models

## Gemma Models and Hebrew

**Gemma 2B/7B** (Google):
- ✅ **Multilingual support** - Trained on multilingual data
- ⚠️ **Hebrew**: Limited support - not specifically optimized for Hebrew
- **Model**: `google/gemma-2-2b-it` or `google/gemma-2-7b-it`
- **Note**: There is no "Gemma 3" - latest is Gemma 2

## Better Options for Hebrew

### 1. **Mistral 7B** (Recommended)
- ✅ Excellent multilingual support
- ✅ Good Hebrew understanding
- ✅ Better than Gemma for Hebrew
- **Model**: `mistralai/Mistral-7B-Instruct-v0.2`

### 2. **Llama 2/3** (Meta)
- ✅ Good multilingual support
- ✅ Decent Hebrew
- ⚠️ Requires approval for some models
- **Model**: `meta-llama/Llama-2-7b-chat-hf`

### 3. **Hebrew-Specific Models**
- `ai21labs/J1-Large` - Has Hebrew support
- `OpenBuddy/openbuddy-llama2-13b-v8.1-fp16` - Multilingual with Hebrew

### 4. **Qwen Models** (Alibaba)
- ✅ Excellent multilingual including Hebrew
- ✅ Good instruction following
- **Model**: `Qwen/Qwen2-1.5B-Instruct` or `Qwen/Qwen2-7B-Instruct`

## Recommendation for Your Use Case

For Hebrew documents (like your contract), I recommend:

1. **Mistral 7B** - Best balance of quality and Hebrew support
2. **Qwen 2 7B** - Excellent multilingual, good Hebrew
3. **Gemma 2 7B** - Works but not optimal for Hebrew

## Testing Hebrew Support

To test if a model supports Hebrew well, try:
- Simple Hebrew questions
- Hebrew text generation
- Hebrew instruction following

## Update Your Config

If you want to switch to a better Hebrew model, update `.env`:

```env
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.2
```

Or for smaller model:
```env
HF_MODEL=Qwen/Qwen2-1.5B-Instruct
```
