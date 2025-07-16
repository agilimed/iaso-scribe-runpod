# IASO Scribe - RunPod Serverless Deployment

This is a RunPod serverless worker that combines Whisper speech-to-text with **Phi-4-reasoning-plus** using GGUF Q6_K_L quantization for optimal quality and performance.

## Features

- **Whisper Large-v3**: State-of-the-art speech recognition
- **Phi-4-reasoning-plus Q6_K_L**: Microsoft's most advanced reasoning model
  - Uses Q8_0 for embed and output weights
  - Very high quality, near perfect accuracy
  - 12.28GB model size (efficient for 16GB+ GPUs)
- **GGUF Quantization**: Optimal balance of quality and performance
- **GPU Acceleration**: Full CUDA support via llama.cpp
- **Serverless**: Scales to zero, pay only for usage
- **Advanced Medical Reasoning**: Superior clinical analysis and documentation

## Quick Deployment (2025)

### Deploy from GitHub (Recommended)

1. **Connect GitHub to RunPod**
   - Go to [RunPod Settings](https://runpod.io/console/settings)
   - Connect your GitHub account

2. **Deploy Endpoint**
   - Go to [RunPod Serverless](https://runpod.io/console/serverless)
   - Click "Deploy New Endpoint" → "GitHub Repo"
   - Select: `vivek-agilimed/iaso-scribe-runpod`
   - GPU: 16GB VRAM (RTX 4070 Ti for Community Cloud savings)
   - Min Workers: 0, Max Workers: 3

3. **Environment Variables**
   ```
   WHISPER_MODEL=large-v3
   PHI_MODEL_PATH=/models/Phi-4-reasoning-plus-Q6_K_L.gguf
   ```

See [DEPLOY_NOW_2025.md](DEPLOY_NOW_2025.md) for detailed instructions.

## Configuration

Environment variables:
- `WHISPER_MODEL`: Whisper model size (default: large-v3)
- `PHI_MODEL_PATH`: Path to Phi-4-reasoning-plus GGUF model (default: /models/Phi-4-reasoning-plus-Q6_K_L.gguf)
- `PHI_MODEL_URL`: URL to download model from (default: HuggingFace bartowski repo)

## API Usage

```json
{
  "input": {
    "audio": "https://example.com/audio.wav",
    "language": "en",
    "generate_insights": true,
    "return_segments": false
  }
}
```

Response:
```json
{
  "transcription": "Patient presents with...",
  "language": "en",
  "duration": 30.5,
  "medical_insights": "Key findings: ..."
}
```

## Model Information

### Whisper Large-v3
- Latest and most accurate Whisper model
- Excellent multilingual support
- Real-time transcription capabilities

### Phi-4-reasoning-plus (14B parameters)
- **Model**: [microsoft/Phi-4-reasoning-plus](https://huggingface.co/microsoft/Phi-4-reasoning-plus)
- **Quantization**: [Q6_K_L GGUF by bartowski](https://huggingface.co/bartowski/microsoft_Phi-4-reasoning-plus-GGUF)
- **Size**: 12.28GB (vs 28GB+ unquantized)
- **Quality**: Near-perfect accuracy with Q8_0 embed/output weights
- **Performance**: Optimized for GPU inference via llama.cpp

### Why Phi-4-reasoning-plus Q6_K_L?

1. **Superior Reasoning**: Phi-4-reasoning-plus is specifically designed for complex analytical tasks
2. **Medical Expertise**: Enhanced capabilities for clinical documentation and reasoning
3. **Optimal Quantization**: Q6_K_L provides the best quality/performance ratio
4. **GPU Efficient**: Fits comfortably on 16GB GPUs (RTX 4060 Ti, A4000, etc.)
5. **Production Ready**: Stable, well-tested quantization format

## Cost Optimization

- Models are loaded once and reused across requests
- Automatic scaling to zero when idle
- Efficient model quantization for reduced memory usage