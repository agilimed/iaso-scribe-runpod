# RunPod Infrastructure

This directory contains all RunPod deployment configurations and Dockerfiles for IASO services.

## Directory Structure

```
infrastructure/runpod/
├── whisper/         # Whisper ASR service
│   └── Dockerfile
├── phi4/           # Phi-4 summarization service  
│   └── Dockerfile
├── iasoql/         # IASOQL text-to-SQL service
│   └── Dockerfile
└── README.md       # This file
```

## Deployed Services

### 1. Whisper (Speech-to-Text)
- **Endpoint ID**: rntxttrdl8uv3i
- **Model**: openai/whisper-large-v3
- **Purpose**: Audio transcription for IasoScribe

### 2. Phi-4 (Medical Summarization)
- **Endpoint ID**: tmmwa4q8ax5sg4
- **Model**: microsoft/phi-4
- **Purpose**: Medical document summarization

### 3. IASOQL (Text-to-SQL)
- **Endpoint ID**: 86sthoj37yewbq
- **Model**: vivkris/iasoql-7B (private HuggingFace)
- **Purpose**: Healthcare SQL generation for ClickHouse

## Environment Variables

Set these in your `.env` file:

```bash
RUNPOD_API_KEY=your_api_key_here
WHISPER_ENDPOINT_ID=rntxttrdl8uv3i
PHI4_ENDPOINT_ID=tmmwa4q8ax5sg4
IASOQL_ENDPOINT_ID=86sthoj37yewbq
```

## Testing

Test scripts are located in `/scripts/test/`:
- `test_iasoql_endpoint.py` - Test IASOQL endpoint
- `test_iasoql_working.py` - Working IASOQL test

## Deployment

All services are deployed via GitHub integration with RunPod:
1. Push changes to GitHub repo: https://github.com/agilimed/iaso-scribe-runpod
2. RunPod automatically builds and deploys from the respective directories

## Updating RunPod Endpoints

To update the GitHub repository for all endpoints:

1. Go to https://www.runpod.io/console/serverless
2. For each endpoint (Whisper, Phi-4, IASOQL):
   - Click on the endpoint
   - Go to "Settings" tab
   - Under "Source", update the GitHub URL to: `https://github.com/agilimed/iaso-scribe-runpod`
   - Keep the same build context paths:
     - Whisper: `/whisper`
     - Phi-4: `/phi4`
     - IASOQL: `/iasoql`
   - Click "Save" to trigger a rebuild