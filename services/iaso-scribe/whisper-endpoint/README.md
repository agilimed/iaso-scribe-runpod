# Whisper Medium Endpoint for RunPod

Simple, clean implementation of Whisper Medium using faster-whisper on RunPod serverless.

## Features
- Whisper Medium model
- GPU acceleration with CUDA
- VAD (Voice Activity Detection) enabled
- Supports URL and base64 audio input
- Optional segment timestamps

## API

```json
{
  "input": {
    "audio": "https://example.com/audio.wav",
    "language": "en",
    "return_segments": false
  }
}
```

## Response

```json
{
  "transcription": "The transcribed text",
  "language": "en",
  "duration": 10.5,
  "processing_time": 2.3
}
```