# Deploy IASO Scribe to RunPod via GitHub (No Local Build Required!)

This guide shows how to deploy directly to RunPod using their GitHub integration - no local Docker builds needed!

## 🚀 Quick Deploy Steps

### 1. Prepare Your GitHub Repository

Push the IASO Scribe RunPod code to a GitHub repository:

```bash
cd /Users/vivekkrishnan/dev/iaso/services/iaso-scribe/runpod

# If not already a git repo, initialize it
git init
git add .
git commit -m "IASO Scribe with Phi-4-reasoning-plus and Whisper"

# Create a new GitHub repo and push
# Option 1: Using GitHub CLI
gh repo create iaso-scribe-runpod --public --source=. --remote=origin --push

# Option 2: Manual
# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/iaso-scribe-runpod.git
git push -u origin main
```

### 2. Connect RunPod to GitHub

1. Go to [RunPod Console Settings](https://runpod.io/console/settings)
2. Find the **GitHub** card under **Connections**
3. Click **Connect** and authorize RunPod

### 3. Deploy from GitHub

1. Go to [Deploy New Serverless Endpoint](https://runpod.io/console/serverless)
2. Click **GitHub Repo** (bottom right)
3. Select your repository: `iaso-scribe-runpod`
4. Configure:
   - **Endpoint Name**: `iaso-scribe-phi4`
   - **GPU Type**: RTX A4000 (16GB) or better
   - **Min Workers**: 0 (scales to zero)
   - **Max Workers**: 3-5
   - **Idle Timeout**: 5 seconds
   - **Flash Boot**: Enabled

5. Set Environment Variables:
   ```
   WHISPER_MODEL=large-v3
   PHI_MODEL_PATH=/models/Phi-4-reasoning-plus-Q6_K_L.gguf
   ```

6. Click **Deploy**

RunPod will:
- Pull your code from GitHub
- Build the Docker image on their infrastructure
- Store it in their registry
- Deploy your endpoint

## 📁 Required Files

Your GitHub repo must contain:
- `handler.py` - The serverless handler
- `Dockerfile` - Build instructions
- `requirements.txt` - Python dependencies
- `.dockerignore` - Exclude unnecessary files

## 🎯 Benefits

1. **No Local Build** - RunPod builds everything
2. **No Upload** - No pushing to Docker Hub
3. **Automatic** - Push to GitHub = Deploy to RunPod
4. **Fast Updates** - Just push code changes

## 🔄 Updating Your Deployment

To update your deployed endpoint:

```bash
# Make changes to your code
git add .
git commit -m "Update: improved medical reasoning"
git push

# In RunPod Console:
# Go to your endpoint and click "Redeploy"
```

## 📊 First Run Note

The first request will download the Phi-4-reasoning-plus model (12.28GB). Subsequent requests will be fast as the model is cached.

## 🧪 Testing

Once deployed, test with:

```bash
ENDPOINT_ID="your-endpoint-id"
RUNPOD_API_KEY="your-api-key"

curl -X POST "https://api.runpod.ai/v2/${ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "audio": "https://example.com/medical-audio.wav",
      "generate_insights": true
    }
  }'
```

## 🚨 Important Notes

- Build time limit: 160 minutes
- Image size limit: 100GB
- Models are downloaded on first run (not during build)
- Use RTX A4000 or better for Phi-4-reasoning-plus