# Setup Network Volume for IASO Scribe Models

## Why Network Volume?

Container disk is limited and temporary. For large models like Phi-4 (12.3GB), we need persistent Network Volume storage.

## Step 1: Create Network Volume

1. Go to [RunPod Console](https://runpod.io/console/user/storage)
2. Click "Create Network Volume"
3. Configure:
   ```
   Name: iaso-scribe-models
   Size: 30 GB
   Region: Same as your endpoint
   ```
4. Click "Create"

## Step 2: Attach to Your Endpoint

1. Go to your endpoint settings
2. Under "Storage Configuration":
   - Network Volume: Select `iaso-scribe-models`
   - Mount Path: `/workspace`
3. Save changes

## Step 3: Update Handler to Use Network Volume

The handler needs to use `/workspace` for model storage:

```python
# Update these paths in handler.py
PHI_MODEL_PATH = os.environ.get("PHI_MODEL_PATH", "/workspace/models/Phi-4-reasoning-plus-Q6_K_L.gguf")

# Whisper download root
download_root="/workspace/models/whisper"
```

## Step 4: Environment Variables

Update your endpoint environment variables:
```
WHISPER_MODEL=medium
PHI_MODEL_PATH=/workspace/models/Phi-4-reasoning-plus-Q6_K_L.gguf
```

## Benefits

- **Persistent**: Models stay between deployments
- **Shared**: Can be used by multiple workers
- **Larger**: Up to 10TB available
- **Cost-effective**: Only download models once

## Cost

- Network Volume: ~$0.07/GB/month
- 30GB = ~$2.10/month
- Much cheaper than re-downloading models!