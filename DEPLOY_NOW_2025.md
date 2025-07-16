# 🚀 Deploy IASO Scribe on RunPod NOW! (2025 Guide)

Your GitHub repo is ready at: https://github.com/vivek-agilimed/iaso-scribe-runpod

## Step-by-Step Deployment

### 1. Open RunPod Serverless Console
👉 **Go to:** https://runpod.io/console/serverless

### 2. Click "Deploy New Endpoint"
Look for the blue button on the page

### 3. Select "GitHub Repo" 
Click the **GitHub Repo** option (usually bottom right)

### 4. Choose Your Repository
- Select: `vivek-agilimed/iaso-scribe-runpod`
- Branch: `main`

### 5. Configure Your Endpoint

**Basic Settings:**
```
Endpoint Name: iaso-scribe-phi4
Container Disk: 20 GB
```

**GPU Configuration:**
```
GPU Tier: Select "16 GB VRAM"
Options: 
- RTX 4070 Ti (Community - Cheapest!)
- RTX A4000 (Secure - More stable)
```

**Scaling Settings:**
```
Min Workers: 0 (IMPORTANT - scales to zero!)
Max Workers: 3
Idle Timeout: 5 seconds
Flash Boot: Enabled ✓
```

### 6. Environment Variables (Advanced Settings)
Click "Advanced" and add:
```
WHISPER_MODEL=large-v3
PHI_MODEL_PATH=/models/Phi-4-reasoning-plus-Q6_K_L.gguf
```

### 7. Click "Deploy"

RunPod will now:
1. Pull your code from GitHub
2. Build the Docker image
3. Deploy your endpoint
4. Give you an endpoint URL

## 🧪 Test Your Endpoint

Once deployed, you'll get an endpoint ID. Test it:

```bash
ENDPOINT_ID="your-endpoint-id-here"
RUNPOD_API_KEY="your-api-key-here"

curl -X POST "https://api.runpod.ai/v2/${ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "audio": "https://www2.cs.uic.edu/~i101/SoundFiles/StarWars60.wav",
      "generate_insights": true
    }
  }'
```

## 💡 Cost Tips

- **Community Cloud**: Choose RTX 4070 Ti for 75% savings
- **Scales to Zero**: You pay $0 when not in use
- **First Run**: Will download models (~14GB), be patient

## 📊 What You Get

- **Whisper Large-v3**: Best speech recognition
- **Phi-4-reasoning-plus**: Advanced medical reasoning
- **Q6_K_L Quantization**: Near-perfect quality
- **Serverless**: Pay only when processing

That's it! Your endpoint should be live in 5-10 minutes.