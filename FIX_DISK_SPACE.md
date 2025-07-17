# Fix RunPod Disk Space Issue

## The Problem
Your container ran out of disk space when downloading models:
- Whisper Medium: ~0.5GB
- Phi-4-reasoning-plus: ~12.28GB
- Total needed: ~13GB + OS/dependencies

## Solution: Update Your RunPod Endpoint

### Option 1: Update Existing Endpoint (Recommended)

1. **Go to RunPod Console**
   - https://runpod.io/console/serverless
   - Find your endpoint: `rntxttrdl8uv3i`

2. **Click "Edit" on your endpoint**

3. **Update Container Disk Size**
   ```
   Container Disk: 50 GB
   ```
   (Was 20 GB, needs to be at least 50 GB)

4. **Click "Save Changes"**

5. **Redeploy** (if needed)

### Option 2: Create New Endpoint with Proper Size

If editing doesn't work, create a new endpoint with:
- Container Disk: 50 GB minimum
- All other settings the same

## Disk Space Breakdown

```
Base OS + Python:     ~5 GB
Whisper Medium:       ~0.5 GB
Phi-4 Q6_K_L:        ~12.3 GB
Temp space needed:    ~10 GB (during download)
Safety margin:        ~5 GB
--------------------------
Total Recommended:    40 GB
```

## Test After Fix

Once you've increased the disk space:

```bash
# Test again
export RUNPOD_API_KEY="your-key"
python3 test_deployment.py
```

The download will happen once, then models are cached for all future requests.

## Prevention Tips

1. **Always set Container Disk to 50GB** for LLM deployments
2. **Monitor disk usage** in RunPod console
3. **Consider using network volumes** for model storage (persistent across deploys)