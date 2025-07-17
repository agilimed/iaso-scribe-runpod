# Debugging RunPod Disk Space Issue

## Current Issue
Even with 50GB container disk, still getting "No space left on device" errors.

## Possible Causes

1. **Workers Not Restarted**
   - Changes to disk size may require workers to restart
   - Solution: In RunPod console, scale workers to 0, then back up

2. **Disk Size Not Applied**
   - The change might not have propagated
   - Solution: Redeploy the endpoint

3. **Model Download Location**
   - Models might be downloading to wrong location (e.g., /tmp instead of /models)
   - Our handler uses: `/models/whisper` and `/models/Phi-4-reasoning-plus-Q6_K_L.gguf`

## Steps to Fix

### 1. Force Worker Restart
In RunPod Console:
- Set Min Workers: 0
- Set Max Workers: 0
- Save
- Wait 30 seconds
- Set Min Workers: 0
- Set Max Workers: 2
- Save

### 2. Check in RunPod Console
- Look for "Container Disk" setting
- Verify it shows 50 GB
- Check worker logs for disk space info

### 3. If Still Failing
Consider:
- Creating a new endpoint with 50GB from start
- Using network volume for model storage
- Pre-downloading models in Docker image (but increases build time)

## Alternative: Minimal Test
Try without downloading any models:
```python
# Just echo back the input without processing
{
    "input": {
        "test": "echo",
        "skip_models": true
    }
}
```