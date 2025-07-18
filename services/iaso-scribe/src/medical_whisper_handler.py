"""
IasoScribe Medical Whisper Handler
Optimized for medical transcription with Faster-Whisper
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np

try:
    import runpod
    RUNPOD_AVAILABLE = True
except ImportError:
    RUNPOD_AVAILABLE = False
    
from faster_whisper import WhisperModel
import torch

from medical_vocabulary_enhancer import MedicalVocabularyEnhancer
from audio_preprocessor import AudioPreprocessor
from clinical_ai_integration import ClinicalAIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalWhisperHandler:
    """
    Enhanced Whisper handler for medical transcription
    """
    
    def __init__(self, model_size: str = "medium", device: str = "auto"):
        """
        Initialize the medical whisper handler
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v2, large-v3)
            device: Device to run on (cuda, cpu, auto)
        """
        # Auto-detect device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing Whisper model: {model_size} on {self.device}")
        
        # Initialize Faster-Whisper model
        self.model = WhisperModel(
            model_size, 
            device=self.device,
            compute_type="float16" if self.device == "cuda" else "float32",
            download_root="/models"
        )
        
        # Initialize medical components
        self.vocab_enhancer = MedicalVocabularyEnhancer()
        self.audio_preprocessor = AudioPreprocessor()
        self.clinical_ai = ClinicalAIClient()
        
        # Medical specialty prompts
        self.medical_prompts = {
            "general": "Medical consultation transcript.",
            "cardiology": "Cardiology consultation. Common terms: MI, EKG, echocardiogram, catheterization, stent, arrhythmia, hypertension, CHF.",
            "maternity": "Obstetric consultation. Terms: gravida, para, gestational age, contractions, fetal heart rate, cervical dilation, preeclampsia.",
            "orthopedics": "Orthopedic evaluation. Terms: ROM, arthroscopy, joint replacement, fracture, ligament, tendon, osteoarthritis.",
            "neurology": "Neurology consultation. Terms: seizure, migraine, stroke, TIA, EEG, MRI, neuropathy, multiple sclerosis.",
            "pediatrics": "Pediatric consultation. Terms: immunization, developmental milestones, growth percentile, fever, otitis media.",
            "psychiatry": "Psychiatric evaluation. Terms: depression, anxiety, bipolar, ADHD, cognitive behavioral therapy, SSRI.",
            "emergency": "Emergency department note. Terms: triage, vital signs, chief complaint, differential diagnosis, disposition."
        }
        
        logger.info("Medical Whisper Handler initialized successfully")
    
    def get_medical_prompt(self, specialty: str, context: Optional[Dict] = None) -> str:
        """
        Get specialty-specific prompt for better transcription
        """
        base_prompt = self.medical_prompts.get(specialty, self.medical_prompts["general"])
        
        # Add context-specific information
        if context:
            if context.get("chief_complaint"):
                base_prompt += f" Chief complaint: {context['chief_complaint']}."
            if context.get("known_conditions"):
                conditions = ", ".join(context['known_conditions'])
                base_prompt += f" Known conditions: {conditions}."
                
        return base_prompt
    
    async def transcribe_audio(
        self, 
        audio_path: str, 
        specialty: str = "general",
        context: Optional[Dict] = None,
        language: str = "en",
        enable_vad: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe audio with medical optimization
        
        Args:
            audio_path: Path to audio file
            specialty: Medical specialty for context
            context: Additional medical context
            language: Language code
            enable_vad: Enable voice activity detection
            
        Returns:
            Transcription result with medical enhancements
        """
        start_time = time.time()
        
        # Preprocess audio
        processed_audio = self.audio_preprocessor.process(
            audio_path,
            denoise=True,
            normalize=True
        )
        
        # Get medical prompt
        initial_prompt = self.get_medical_prompt(specialty, context)
        
        # Transcribe with Faster-Whisper
        segments, info = self.model.transcribe(
            processed_audio,
            language=language,
            initial_prompt=initial_prompt,
            beam_size=5,
            best_of=5,
            patience=1,
            length_penalty=1,
            temperature=0,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
            condition_on_previous_text=True,
            vad_filter=enable_vad,
            vad_parameters=dict(
                threshold=0.5,
                min_speech_duration_ms=250,
                max_speech_duration_s=float('inf'),
                min_silence_duration_ms=2000,
                window_size_samples=1024,
                speech_pad_ms=400
            )
        )
        
        # Convert segments to list and build transcript
        segment_list = []
        full_transcript = []
        
        for segment in segments:
            seg_dict = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "confidence": segment.avg_logprob
            }
            segment_list.append(seg_dict)
            full_transcript.append(segment.text.strip())
        
        # Join transcript
        raw_transcript = " ".join(full_transcript)
        
        # Enhance with medical vocabulary
        enhanced_transcript = await self.vocab_enhancer.enhance_transcript(
            raw_transcript,
            specialty=specialty,
            segments=segment_list
        )
        
        # Extract medical entities using Clinical AI
        medical_entities = None
        if await self.clinical_ai.is_available():
            try:
                medical_entities = await self.clinical_ai.extract_entities(
                    enhanced_transcript,
                    specialty=specialty
                )
            except Exception as e:
                logger.warning(f"Clinical AI extraction failed: {e}")
        
        # Calculate metrics
        duration = time.time() - start_time
        audio_duration = segment_list[-1]["end"] if segment_list else 0
        
        result = {
            "transcript": enhanced_transcript,
            "raw_transcript": raw_transcript,
            "segments": segment_list,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": duration,
            "audio_duration": audio_duration,
            "processing_speed": audio_duration / duration if duration > 0 else 0,
            "medical_entities": medical_entities,
            "specialty": specialty,
            "metadata": {
                "model": self.model.model_size,
                "device": self.device,
                "timestamp": datetime.utcnow().isoformat(),
                "vad_enabled": enable_vad
            }
        }
        
        return result
    
    async def generate_medical_note(
        self,
        transcript: str,
        template: str = "soap",
        specialty: str = "general",
        entities: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate structured medical note from transcript
        
        Args:
            transcript: The transcribed text
            template: Note template type (soap, progress, discharge)
            specialty: Medical specialty
            entities: Pre-extracted medical entities
            
        Returns:
            Structured medical note
        """
        # If entities not provided, extract them
        if not entities and await self.clinical_ai.is_available():
            entities = await self.clinical_ai.extract_entities(transcript, specialty)
        
        # Generate structured note based on template
        if template == "soap":
            note = self._generate_soap_note(transcript, entities, specialty)
        elif template == "progress":
            note = self._generate_progress_note(transcript, entities, specialty)
        elif template == "discharge":
            note = self._generate_discharge_note(transcript, entities, specialty)
        else:
            note = {"error": f"Unknown template: {template}"}
        
        return {
            "template": template,
            "specialty": specialty,
            "structured_note": note,
            "entities": entities,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_soap_note(self, transcript: str, entities: Optional[Dict], specialty: str) -> Dict[str, str]:
        """Generate SOAP format note"""
        # This would integrate with your Template Service
        # For now, a simple implementation
        sections = {
            "subjective": "",
            "objective": "",
            "assessment": "",
            "plan": ""
        }
        
        # Parse transcript into sections (simplified)
        lines = transcript.split(". ")
        
        # Basic heuristic parsing
        for line in lines:
            line_lower = line.lower()
            if any(word in line_lower for word in ["complains", "reports", "feels", "states"]):
                sections["subjective"] += line + ". "
            elif any(word in line_lower for word in ["vital", "exam", "appears", "blood pressure"]):
                sections["objective"] += line + ". "
            elif any(word in line_lower for word in ["diagnosis", "impression", "conclude"]):
                sections["assessment"] += line + ". "
            elif any(word in line_lower for word in ["prescribe", "recommend", "follow up", "order"]):
                sections["plan"] += line + ". "
        
        # Clean up sections
        for key in sections:
            sections[key] = sections[key].strip()
            
        return sections
    
    def _generate_progress_note(self, transcript: str, entities: Optional[Dict], specialty: str) -> Dict[str, str]:
        """Generate progress note format"""
        return {
            "chief_complaint": entities.get("chief_complaint", "") if entities else "",
            "hpi": transcript[:500],  # First part as HPI
            "current_medications": entities.get("medications", []) if entities else [],
            "assessment_plan": transcript[500:] if len(transcript) > 500 else ""
        }
    
    def _generate_discharge_note(self, transcript: str, entities: Optional[Dict], specialty: str) -> Dict[str, str]:
        """Generate discharge summary format"""
        return {
            "admission_diagnosis": "",
            "discharge_diagnosis": entities.get("conditions", []) if entities else [],
            "hospital_course": transcript,
            "discharge_medications": entities.get("medications", []) if entities else [],
            "follow_up": ""
        }
    
    async def runpod_handler(self, event: Dict) -> Dict[str, Any]:
        """
        RunPod serverless handler
        
        Args:
            event: RunPod event with job input
            
        Returns:
            Job result
        """
        try:
            job_input = event["input"]
            
            # Extract parameters
            audio_url = job_input.get("audio")
            specialty = job_input.get("medical_context", {}).get("specialty", "general")
            context = job_input.get("medical_context", {})
            language = job_input.get("language", "en")
            generate_note = job_input.get("generate_note", False)
            note_template = job_input.get("note_template", "soap")
            
            # Download audio if URL provided
            if audio_url.startswith("http"):
                audio_path = self.audio_preprocessor.download_audio(audio_url)
            else:
                audio_path = audio_url
            
            # Transcribe
            result = await self.transcribe_audio(
                audio_path=audio_path,
                specialty=specialty,
                context=context,
                language=language
            )
            
            # Generate structured note if requested
            if generate_note:
                note_result = await self.generate_medical_note(
                    transcript=result["transcript"],
                    template=note_template,
                    specialty=specialty,
                    entities=result.get("medical_entities")
                )
                result["structured_note"] = note_result
            
            # Clean up temporary files
            if audio_url.startswith("http"):
                os.remove(audio_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RunPod handler: {str(e)}")
            return {
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat()
            }

# Initialize handler
handler = MedicalWhisperHandler()

# RunPod entry point
if RUNPOD_AVAILABLE:
    runpod.serverless.start({
        "handler": handler.runpod_handler
    })
else:
    logger.info("Running in non-RunPod environment")