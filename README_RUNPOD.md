# IASO Scribe - RunPod Deployment

Deploy Whisper + Phi-4-reasoning-plus directly on RunPod without local builds!

## 🚀 Fastest Deployment Method

### Step 1: Connect GitHub to RunPod
1. Go to [RunPod Settings](https://runpod.io/console/settings)
2. Click "Connect" under GitHub
3. Authorize RunPod

### Step 2: Deploy from GitHub
1. Push this code to your GitHub repo
2. Go to [RunPod Serverless](https://runpod.io/console/serverless)
3. Click "Deploy New Endpoint" → "GitHub Repo"
4. Select your repository
5. Configure:
   - GPU: RTX A4000 (16GB minimum)
   - Workers: 0-3 (scales to zero)
   - Container Disk: 20GB

### Step 3: First Run
The first request downloads models:
- Whisper large-v3 (~1.5GB)
- Phi-4-reasoning-plus Q6_K_L (~12.28GB)

Subsequent requests are fast!

## 📝 What This Does

Combines:
- **Whisper Large-v3**: Best speech recognition
- **Phi-4-reasoning-plus**: Advanced medical reasoning
- **GGUF Q6_K_L**: Near-perfect quality quantization

Perfect for medical transcription with AI-powered insights!

## 🧪 Test Your Endpoint

```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "audio": "https://example.com/audio.wav",
      "generate_insights": true
    }
  }'
```

## 💡 No Docker Required!

RunPod builds everything for you:
- No local Docker installation needed
- No uploading large images
- Just push to GitHub and deploy!

That's it! 🎉