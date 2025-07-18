"""
Clinical AI Integration for IasoScribe
Connects to existing Clinical AI services for medical entity extraction
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ClinicalAIClient:
    """
    Client for integrating with Clinical AI services
    """
    
    def __init__(
        self,
        clinical_ai_url: str = None,
        terminology_url: str = None,
        knowledge_url: str = None,
        template_url: str = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize Clinical AI client
        
        Args:
            clinical_ai_url: Clinical AI service URL
            terminology_url: Terminology service URL
            knowledge_url: Knowledge service URL
            template_url: Template service URL
            api_key: Optional API key for authentication
        """
        # Use environment variables or defaults
        self.clinical_ai_url = clinical_ai_url or os.getenv("CLINICAL_AI_URL", "http://localhost:8002")
        self.terminology_url = terminology_url or os.getenv("TERMINOLOGY_URL", "http://localhost:8001")
        self.knowledge_url = knowledge_url or os.getenv("KNOWLEDGE_URL", "http://localhost:8004")
        self.template_url = template_url or os.getenv("TEMPLATE_URL", "http://localhost:8003")
        
        self.api_key = api_key or os.getenv("CLINICAL_AI_API_KEY")
        
        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
        
        # Headers
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Cache for service availability
        self._service_available = {
            "clinical_ai": None,
            "terminology": None,
            "knowledge": None,
            "template": None
        }
        
        logger.info("Clinical AI client initialized")
    
    async def is_available(self) -> bool:
        """
        Check if Clinical AI services are available
        """
        # Check service health with timeout
        try:
            return await self._check_service_health("clinical_ai", self.clinical_ai_url)
        except Exception:
            return False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def extract_entities(
        self,
        text: str,
        specialty: str = "general",
        extract_embeddings: bool = False,
        link_to_umls: bool = True
    ) -> Dict[str, Any]:
        """
        Extract medical entities using Clinical AI service
        
        Args:
            text: Text to analyze
            specialty: Medical specialty context
            extract_embeddings: Whether to extract embeddings
            link_to_umls: Link entities to UMLS concepts
            
        Returns:
            Extracted entities with metadata
        """
        try:
            # Check service availability
            if not await self._check_service_health("clinical_ai", self.clinical_ai_url):
                logger.warning("Clinical AI service unavailable")
                return self._get_fallback_entities(text)
            
            # Prepare request
            request_data = {
                "text": text,
                "extract_embeddings": extract_embeddings,
                "link_to_umls": link_to_umls,
                "context": {
                    "specialty": specialty,
                    "source": "transcription"
                }
            }
            
            # Make request
            response = await self.client.post(
                f"{self.clinical_ai_url}/extract",
                json=request_data,
                headers=self.headers
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Enhance result with additional metadata
            result["extraction_timestamp"] = datetime.utcnow().isoformat()
            result["specialty"] = specialty
            
            return result
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return self._get_fallback_entities(text)
    
    async def search_terminology(
        self,
        term: str,
        limit: int = 5,
        semantic_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for medical terms using Terminology service
        
        Args:
            term: Search term
            limit: Maximum results
            semantic_types: Filter by semantic types
            
        Returns:
            List of matching concepts
        """
        try:
            params = {
                "term": term,
                "limit": limit
            }
            
            if semantic_types:
                params["semantic_types"] = ",".join(semantic_types)
            
            response = await self.client.get(
                f"{self.terminology_url}/search",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Terminology search failed: {e}")
            return []
    
    async def validate_medical_term(self, term: str) -> Optional[Dict[str, Any]]:
        """
        Validate a single medical term
        
        Args:
            term: Term to validate
            
        Returns:
            Validated concept or None
        """
        results = await self.search_terminology(term, limit=1)
        return results[0] if results else None
    
    async def get_concept_relationships(
        self,
        cui: str,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for a medical concept
        
        Args:
            cui: Concept Unique Identifier
            relationship_types: Filter by relationship types
            
        Returns:
            List of related concepts
        """
        try:
            params = {}
            if relationship_types:
                params["rel_types"] = ",".join(relationship_types)
            
            response = await self.client.get(
                f"{self.knowledge_url}/concepts/{cui}/relationships",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get concept relationships: {e}")
            return []
    
    async def generate_clinical_note(
        self,
        transcript: str,
        template_type: str = "soap",
        entities: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate structured clinical note using Template service
        
        Args:
            transcript: Transcribed text
            template_type: Type of note (soap, progress, discharge)
            entities: Pre-extracted entities
            metadata: Additional metadata
            
        Returns:
            Structured clinical note
        """
        try:
            request_data = {
                "text": transcript,
                "template": template_type,
                "entities": entities,
                "metadata": metadata or {}
            }
            
            response = await self.client.post(
                f"{self.template_url}/generate",
                json=request_data,
                headers=self.headers
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to generate clinical note: {e}")
            return {
                "error": str(e),
                "template": template_type,
                "generated": False
            }
    
    async def enhance_transcription_context(
        self,
        text: str,
        specialty: str
    ) -> Dict[str, Any]:
        """
        Enhance transcription with full clinical context
        
        This combines multiple services for comprehensive enhancement:
        1. Entity extraction
        2. Terminology validation
        3. Concept relationships
        
        Args:
            text: Transcribed text
            specialty: Medical specialty
            
        Returns:
            Enhanced context with entities, validations, and relationships
        """
        # Extract entities
        entities = await self.extract_entities(text, specialty)
        
        # Validate and enhance key terms
        enhanced_entities = {}
        
        # Process medications
        if "medications" in entities.get("entities", {}):
            enhanced_meds = []
            for med in entities["entities"]["medications"]:
                if isinstance(med, dict) and "drug_name" in med:
                    # Validate drug name
                    validated = await self.validate_medical_term(med["drug_name"])
                    if validated:
                        med["validated_cui"] = validated.get("cui")
                        med["preferred_name"] = validated.get("preferred_name")
                    enhanced_meds.append(med)
            enhanced_entities["medications"] = enhanced_meds
        
        # Process conditions
        if "conditions" in entities.get("entities", {}):
            enhanced_conditions = []
            for condition in entities["entities"]["conditions"]:
                if isinstance(condition, dict) and "text" in condition:
                    # Get relationships for important conditions
                    if condition.get("cui"):
                        relationships = await self.get_concept_relationships(
                            condition["cui"],
                            relationship_types=["is_a", "associated_with"]
                        )
                        condition["relationships"] = relationships[:3]  # Top 3
                    enhanced_conditions.append(condition)
            enhanced_entities["conditions"] = enhanced_conditions
        
        return {
            "original_entities": entities,
            "enhanced_entities": enhanced_entities,
            "specialty": specialty,
            "enhancement_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _check_service_health(self, service_name: str, url: str) -> bool:
        """
        Check if a service is healthy
        """
        try:
            response = await self.client.get(
                f"{url}/health",
                timeout=httpx.Timeout(5.0)
            )
            is_healthy = response.status_code == 200
            self._service_available[service_name] = is_healthy
            return is_healthy
        except Exception:
            self._service_available[service_name] = False
            return False
    
    def _get_fallback_entities(self, text: str) -> Dict[str, Any]:
        """
        Fallback entity extraction using simple patterns
        """
        # Basic pattern matching for common medical terms
        entities = {
            "entities": {
                "conditions": [],
                "medications": [],
                "symptoms": []
            },
            "fallback_mode": True,
            "extraction_timestamp": datetime.utcnow().isoformat()
        }
        
        # Simple medication patterns
        med_patterns = [
            r'\b(\w+)\s+(\d+)\s*(mg|mcg|ml|units?)\b',
            r'\b(aspirin|ibuprofen|acetaminophen|metformin|lisinopril|atorvastatin)\b'
        ]
        
        # Add basic pattern matching here if needed
        
        return entities
    
    async def close(self):
        """
        Close HTTP client
        """
        await self.client.aclose()
    
    async def __aenter__(self):
        """
        Async context manager entry
        """
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit
        """
        await self.close()