# Phi-4 Reasoning Plus Endpoint for RunPod

Medical reasoning using Phi-4-reasoning-plus Q6_K_L quantized model.

## Features
- Phi-4-reasoning-plus Q6_K_L (12.28GB)
- GPU acceleration with llama-cpp-python
- 16K context window
- Medical insights generation
- Step-by-step reasoning

## API

```json
{
  "input": {
    "text": "Patient medical transcription...",
    "prompt_type": "medical_insights",
    "max_tokens": 1024
  }
}
```

## Response

```json
{
  "insights": "Generated medical analysis with reasoning...",
  "processing_time": 15.2,
  "tokens_generated": 512,
  "model": "phi-4-reasoning-plus-Q6_K_L"
}
```