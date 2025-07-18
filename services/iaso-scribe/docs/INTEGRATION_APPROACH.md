# IasoScribe Integration with Clinical AI Services

## How the Medical Vocabulary Enhancer Works

The Medical Vocabulary Enhancer uses a **4-stage pipeline** to improve transcription accuracy:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        IasoScribe Transcription Pipeline                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Whisper ASR          2. Local Corrections      3. Clinical AI       │
│  ┌─────────────┐        ┌──────────────────┐     ┌─────────────────┐  │
│  │   Audio     │        │  - Abbreviations │     │ Entity Extract  │  │
│  │     ↓       │        │  - Common terms  │     │ - Conditions    │  │
│  │ Raw Text    │───────►│  - Drug names    │────►│ - Medications   │  │
│  │             │        │  - Dosages       │     │ - Procedures    │  │
│  └─────────────┘        └──────────────────┘     └─────────────────┘  │
│                                                            │             │
│                                                            ↓             │
│  4. Terminology Service  5. Final Output                                │
│  ┌─────────────────┐    ┌──────────────────┐     ┌─────────────────┐  │
│  │ UMLS Validation │    │ Enhanced         │     │ Structured Note │  │
│  │ - Verify terms  │───►│ Transcript       │────►│ (SOAP/Progress) │  │
│  │ - Get CUIs      │    │ + Entities       │     │                 │  │
│  └─────────────┘        └──────────────────┘     └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Stage 1: Whisper ASR (Audio → Raw Text)
- Uses Faster-Whisper for efficient transcription
- Medical context prompting (specialty-specific)
- Voice Activity Detection (VAD) for clean audio segments

## Stage 2: Local Corrections (Fast, Offline)
The enhancer applies immediate corrections without network calls:

### Medical Abbreviations
- **Input**: "The patient has mi and chf"
- **Output**: "The patient has MI and CHF"

### Common Medical Terms
- **Input**: "prescribed water pill for high blood pressure"
- **Output**: "prescribed diuretic for hypertension"

### Phonetic Drug Corrections
- **Input**: "metaprolol 25 milligrams twice daily"
- **Output**: "metoprolol 25 mg BID"

### Dosage Standardization
- **Input**: "aspirin 81 milligrams"
- **Output**: "aspirin 81 mg"

## Stage 3: Clinical AI Entity Extraction
Sends the locally-corrected text to Clinical AI service:

### Request:
```json
POST http://localhost:8002/extract
{
  "text": "Patient has MI and CHF, prescribed metoprolol 25 mg BID",
  "link_to_umls": true,
  "specialty": "cardiology"
}
```

### Response:
```json
{
  "entities": {
    "conditions": [
      {
        "text": "MI",
        "preferred_term": "Myocardial Infarction",
        "cui": "C0027051",
        "semantic_type": "Disease or Syndrome",
        "start_char": 12,
        "end_char": 14
      },
      {
        "text": "CHF",
        "preferred_term": "Congestive Heart Failure",
        "cui": "C0018802",
        "semantic_type": "Disease or Syndrome",
        "start_char": 19,
        "end_char": 22
      }
    ],
    "medications": [
      {
        "text": "metoprolol 25 mg",
        "drug_name": "metoprolol",
        "dosage": "25 mg",
        "frequency": "BID",
        "cui": "C0025859",
        "validated": true
      }
    ]
  }
}
```

## Stage 4: Terminology Service Validation
Pattern matches the entire text for additional medical terms:

### Request:
```json
POST http://localhost:8001/pattern_match
{
  "text": "Patient has Myocardial Infarction and Congestive Heart Failure",
  "min_term_length": 3,
  "score_threshold": 0.8,
  "semantic_types": ["Disease or Syndrome", "Pharmacologic Substance"]
}
```

### Response:
```json
{
  "matches": [
    {
      "term": "Myocardial Infarction",
      "cui": "C0027051",
      "preferred_name": "Myocardial Infarction",
      "confidence": 1.0,
      "start": 12,
      "end": 33
    }
  ]
}
```

## Real-World Example

### Original Audio Transcription:
```
"The patient is a 65 year old male with a history of m.i. and c.h.f. 
currently on metaprolol 25 milligrams twice a day and lysinopril 
10 milligrams daily. His last echo showed an e.f. of 35 percent. 
Blood pressure today is 130 over 80. He denies chest pain but 
reports some s.o.b. with exertion."
```

### After Enhancement:
```
"The patient is a 65-year-old male with a history of myocardial 
infarction and congestive heart failure currently on metoprolol 
25 mg BID and lisinopril 10 mg daily. His last echocardiogram 
showed an ejection fraction of 35%. Blood pressure today is 
130/80. He denies chest pain but reports some shortness of 
breath with exertion."
```

### Extracted Entities:
```json
{
  "conditions": [
    {"text": "myocardial infarction", "cui": "C0027051"},
    {"text": "congestive heart failure", "cui": "C0018802"},
    {"text": "shortness of breath", "cui": "C0013404", "context": "positive"}
  ],
  "medications": [
    {"drug": "metoprolol", "dose": "25 mg", "frequency": "BID"},
    {"drug": "lisinopril", "dose": "10 mg", "frequency": "daily"}
  ],
  "vitals": [
    {"name": "blood pressure", "value": "130/80", "unit": "mmHg"}
  ],
  "diagnostic_tests": [
    {"name": "echocardiogram", "result": "EF 35%"}
  ],
  "symptoms": [
    {"name": "chest pain", "context": "negative"},
    {"name": "shortness of breath", "context": "positive", "qualifier": "with exertion"}
  ]
}
```

## Performance Optimizations

1. **Local-First Approach**: Common corrections happen instantly without API calls
2. **Async Processing**: Clinical AI and Terminology calls happen in parallel
3. **Caching**: Frequently validated terms are cached (LRU cache)
4. **Batch Processing**: Multiple segments can be processed together
5. **Fallback Logic**: If services are down, local corrections still work

## Configuration Options

```python
# Initialize with custom endpoints
enhancer = MedicalVocabularyEnhancer(
    clinical_ai_url="http://clinical-ai:8002",
    terminology_url="http://terminology:8001"
)

# Enhance with specialty context
enhanced_text = await enhancer.enhance_transcript(
    transcript=raw_text,
    specialty="cardiology",  # Helps with context-specific corrections
    segments=whisper_segments  # Preserves timing information
)
```

## Benefits of This Approach

1. **Accuracy**: Leverages validated medical vocabularies and UMLS
2. **Speed**: Local corrections happen instantly
3. **Reliability**: Works even if some services are unavailable
4. **Context-Aware**: Uses specialty-specific knowledge
5. **Comprehensive**: Handles abbreviations, drugs, dosages, and medical terms
6. **Validated**: All medical terms are verified against UMLS

This integration approach ensures that IasoScribe produces highly accurate medical transcriptions by combining the speed of Whisper with the medical knowledge of your Clinical AI services.