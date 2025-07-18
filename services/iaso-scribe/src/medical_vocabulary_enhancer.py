"""
Medical Vocabulary Enhancer for IasoScribe
Leverages existing Clinical AI services for medical term validation and enhancement
"""

import re
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict
import httpx
from functools import lru_cache

logger = logging.getLogger(__name__)

class MedicalVocabularyEnhancer:
    """
    Enhances transcribed text with medical vocabulary validation and correction
    using existing Clinical AI services
    """
    
    def __init__(self, clinical_ai_url: str = "http://localhost:8002", 
                 terminology_url: str = "http://localhost:8001"):
        """
        Initialize with Clinical AI service endpoints
        """
        self.clinical_ai_url = clinical_ai_url
        self.terminology_url = terminology_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Initialize local medical vocabularies from Clinical AI rules
        self._init_local_vocabularies()
        
        # Cache for terminology lookups
        self._term_cache = {}
        self._pattern_cache = {}
        
    def _init_local_vocabularies(self):
        """
        Initialize local medical vocabularies based on Clinical AI rules.py
        These provide fast, offline validation before hitting the services
        """
        # Common medical abbreviations that Whisper might misinterpret
        self.medical_abbreviations = {
            "mi": "MI",  # Myocardial Infarction
            "chf": "CHF",  # Congestive Heart Failure
            "copd": "COPD",  # Chronic Obstructive Pulmonary Disease
            "uti": "UTI",  # Urinary Tract Infection
            "cad": "CAD",  # Coronary Artery Disease
            "dvt": "DVT",  # Deep Vein Thrombosis
            "pe": "PE",  # Pulmonary Embolism
            "gi": "GI",  # Gastrointestinal
            "iv": "IV",  # Intravenous
            "po": "PO",  # Per Os (by mouth)
            "prn": "PRN",  # As Needed
            "bid": "BID",  # Twice Daily
            "tid": "TID",  # Three Times Daily
            "qid": "QID",  # Four Times Daily
            "hs": "HS",  # At Bedtime
            "npo": "NPO",  # Nothing by Mouth
            "wbc": "WBC",  # White Blood Cell
            "rbc": "RBC",  # Red Blood Cell
            "hgb": "Hgb",  # Hemoglobin
            "hct": "Hct",  # Hematocrit
            "plt": "PLT",  # Platelet
            "inr": "INR",  # International Normalized Ratio
            "pt": "PT",  # Prothrombin Time
            "ptt": "PTT",  # Partial Thromboplastin Time
            "bun": "BUN",  # Blood Urea Nitrogen
            "cr": "Cr",  # Creatinine
            "na": "Na",  # Sodium
            "k": "K",  # Potassium
            "cl": "Cl",  # Chloride
            "co2": "CO2",  # Carbon Dioxide
            "ast": "AST",  # Aspartate Aminotransferase
            "alt": "ALT",  # Alanine Aminotransferase
            "alk phos": "Alk Phos",  # Alkaline Phosphatase
        }
        
        # Common medical terms that need correction
        self.common_corrections = {
            # Whisper might hear -> Correct medical term
            "myocardial infarction": "myocardial infarction",
            "heart attack": "myocardial infarction",
            "sugar diabetes": "diabetes mellitus",
            "high blood pressure": "hypertension",
            "low blood pressure": "hypotension",
            "water pill": "diuretic",
            "blood thinner": "anticoagulant",
            "pain killer": "analgesic",
            "anti inflammatory": "anti-inflammatory",
            "x ray": "X-ray",
            "cat scan": "CT scan",
            "mri scan": "MRI",
            "echo cardiogram": "echocardiogram",
            "electro cardiogram": "electrocardiogram",
            "ekg": "EKG",
            "ecg": "ECG",
        }
        
        # Phonetically similar medical terms (common Whisper mistakes)
        self.phonetic_corrections = {
            "metoprolol": ["metaprolol", "metoprolal", "metropolol"],
            "lisinopril": ["lysinopril", "lisonopril", "lisinopril"],
            "atorvastatin": ["atorvastatin", "atorvastatine", "atorvastaton"],
            "omeprazole": ["omeprazol", "omeprazole", "omeprasol"],
            "furosemide": ["furosemide", "furosimide", "furosemid"],
            "warfarin": ["warfarin", "warfarine", "warfaran"],
            "clopidogrel": ["clopidogrel", "clopidogral", "clopidogril"],
            "metformin": ["metformin", "metformine", "metaformin"],
            "amlodipine": ["amlodipine", "amlodipene", "amlodipine"],
            "simvastatin": ["simvastatin", "simvastatine", "simvastaton"],
        }
        
        # Build reverse lookup for phonetic corrections
        self.phonetic_lookup = {}
        for correct, variants in self.phonetic_corrections.items():
            for variant in variants:
                self.phonetic_lookup[variant.lower()] = correct
    
    async def enhance_transcript(
        self, 
        transcript: str, 
        specialty: str = "general",
        segments: Optional[List[Dict]] = None
    ) -> str:
        """
        Enhance transcript with medical vocabulary corrections
        
        This method:
        1. Corrects common medical abbreviations and terms
        2. Validates medical terms using Clinical AI services
        3. Applies phonetic corrections for commonly misheard drugs
        4. Preserves segment timing if provided
        
        Args:
            transcript: Raw transcript from Whisper
            specialty: Medical specialty for context
            segments: Optional segment information with timing
            
        Returns:
            Enhanced transcript with corrected medical terms
        """
        # Step 1: Apply local corrections (fast)
        enhanced = self._apply_local_corrections(transcript)
        
        # Step 2: Extract and validate medical entities using Clinical AI
        try:
            entities = await self._extract_medical_entities(enhanced, specialty)
            enhanced = await self._apply_entity_corrections(enhanced, entities)
        except Exception as e:
            logger.warning(f"Clinical AI extraction failed, using local rules only: {e}")
        
        # Step 3: Validate medical terms using Terminology Service
        try:
            validated_terms = await self._validate_medical_terms(enhanced)
            enhanced = self._apply_terminology_corrections(enhanced, validated_terms)
        except Exception as e:
            logger.warning(f"Terminology validation failed: {e}")
        
        # Step 4: Apply segment-level corrections if segments provided
        if segments:
            enhanced = self._enhance_segments(enhanced, segments)
        
        return enhanced
    
    def _apply_local_corrections(self, text: str) -> str:
        """
        Apply fast local corrections using predefined rules
        """
        # Convert to working copy
        working_text = text
        
        # Step 1: Fix medical abbreviations (case-insensitive)
        for abbrev, correct in self.medical_abbreviations.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            working_text = re.sub(pattern, correct, working_text, flags=re.IGNORECASE)
        
        # Step 2: Apply common corrections
        for incorrect, correct in self.common_corrections.items():
            pattern = r'\b' + re.escape(incorrect) + r'\b'
            working_text = re.sub(pattern, correct, working_text, flags=re.IGNORECASE)
        
        # Step 3: Fix phonetic drug name errors
        words = working_text.split()
        corrected_words = []
        for word in words:
            word_lower = word.lower().strip('.,!?;:')
            if word_lower in self.phonetic_lookup:
                # Preserve original capitalization pattern
                if word.isupper():
                    corrected_words.append(self.phonetic_lookup[word_lower].upper())
                elif word[0].isupper():
                    corrected_words.append(self.phonetic_lookup[word_lower].capitalize())
                else:
                    corrected_words.append(self.phonetic_lookup[word_lower])
            else:
                corrected_words.append(word)
        
        working_text = ' '.join(corrected_words)
        
        # Step 4: Fix dosage patterns (e.g., "25 milligrams" -> "25 mg")
        dosage_patterns = [
            (r'(\d+\.?\d*)\s*milligrams?\b', r'\1 mg'),
            (r'(\d+\.?\d*)\s*milliters?\b', r'\1 mL'),
            (r'(\d+\.?\d*)\s*micrograms?\b', r'\1 mcg'),
            (r'(\d+\.?\d*)\s*grams?\b', r'\1 g'),
            (r'(\d+\.?\d*)\s*units?\b', r'\1 units'),
        ]
        
        for pattern, replacement in dosage_patterns:
            working_text = re.sub(pattern, replacement, working_text, flags=re.IGNORECASE)
        
        return working_text
    
    async def _extract_medical_entities(self, text: str, specialty: str) -> Dict[str, Any]:
        """
        Extract medical entities using Clinical AI service
        """
        try:
            response = await self.client.post(
                f"{self.clinical_ai_url}/extract",
                json={
                    "text": text,
                    "extract_embeddings": False,
                    "link_to_umls": True,
                    "specialty": specialty
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to extract medical entities: {e}")
            return {}
    
    async def _apply_entity_corrections(self, text: str, entities: Dict[str, Any]) -> str:
        """
        Apply corrections based on extracted medical entities
        """
        if not entities or "entities" not in entities:
            return text
        
        corrections = []
        
        # Process each entity type
        for entity_type, entity_list in entities["entities"].items():
            if not isinstance(entity_list, list):
                continue
                
            for entity in entity_list:
                if not isinstance(entity, dict):
                    continue
                    
                # Get the original text and the validated term
                original_text = entity.get("text", "")
                validated_term = entity.get("preferred_term") or entity.get("validated_name") or original_text
                
                # If Clinical AI provided a preferred term, use it
                if original_text.lower() != validated_term.lower():
                    start = entity.get("start_char")
                    end = entity.get("end_char")
                    if start is not None and end is not None:
                        corrections.append((start, end, validated_term))
        
        # Apply corrections in reverse order to maintain positions
        corrections.sort(key=lambda x: x[0], reverse=True)
        
        working_text = text
        for start, end, replacement in corrections:
            working_text = working_text[:start] + replacement + working_text[end:]
        
        return working_text
    
    async def _validate_medical_terms(self, text: str) -> List[Dict[str, Any]]:
        """
        Validate medical terms using Terminology Service pattern matching
        """
        try:
            response = await self.client.post(
                f"{self.terminology_url}/pattern_match",
                json={
                    "text": text,
                    "min_term_length": 3,
                    "score_threshold": 0.8,
                    "semantic_types": [
                        "Disease or Syndrome",
                        "Pharmacologic Substance",
                        "Laboratory or Test Result",
                        "Clinical Attribute",
                        "Body Part, Organ, or Organ Component"
                    ]
                }
            )
            response.raise_for_status()
            return response.json().get("matches", [])
        except Exception as e:
            logger.error(f"Failed to validate medical terms: {e}")
            return []
    
    def _apply_terminology_corrections(self, text: str, validated_terms: List[Dict]) -> str:
        """
        Apply corrections based on terminology service validation
        """
        if not validated_terms:
            return text
        
        # Sort by position to apply corrections properly
        validated_terms.sort(key=lambda x: x.get("start", 0), reverse=True)
        
        working_text = text
        for term in validated_terms:
            if term.get("confidence", 0) < 0.85:
                continue
                
            start = term.get("start")
            end = term.get("end")
            preferred = term.get("preferred_name")
            
            if start is not None and end is not None and preferred:
                # Only replace if the preferred term is different
                original = working_text[start:end]
                if original.lower() != preferred.lower():
                    # Preserve original capitalization pattern
                    if original.isupper():
                        replacement = preferred.upper()
                    elif original[0].isupper():
                        replacement = preferred.capitalize()
                    else:
                        replacement = preferred.lower()
                    
                    working_text = working_text[:start] + replacement + working_text[end:]
        
        return working_text
    
    def _enhance_segments(self, text: str, segments: List[Dict]) -> str:
        """
        Enhance individual segments while preserving timing information
        """
        # This is useful for maintaining word-level timing accuracy
        # For now, we'll just ensure consistency between full text and segments
        
        # Reconstruct text from enhanced segments
        enhanced_segments = []
        for segment in segments:
            segment_text = segment.get("text", "")
            # Apply local corrections to each segment
            enhanced_segment_text = self._apply_local_corrections(segment_text)
            enhanced_segments.append(enhanced_segment_text)
        
        # Join segments with proper spacing
        return " ".join(enhanced_segments)
    
    @lru_cache(maxsize=1000)
    async def validate_single_term(self, term: str) -> Optional[Dict[str, Any]]:
        """
        Validate a single medical term (cached for performance)
        """
        try:
            response = await self.client.get(
                f"{self.terminology_url}/search",
                params={"term": term, "limit": 1}
            )
            response.raise_for_status()
            results = response.json()
            if results and len(results) > 0:
                return results[0]
        except Exception as e:
            logger.error(f"Failed to validate term '{term}': {e}")
        
        return None
    
    async def close(self):
        """
        Close HTTP client
        """
        await self.client.aclose()