"""
IASOQL MCP Tools - Hybrid SQL Generation with Templates and LLM
"""

from typing import Dict, Any, List, Optional
import httpx
import json
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class IasoQLTools:
    """
    Hybrid SQL generation combining templates and IASOQL LLM
    """
    
    def __init__(self, runpod_api_key: str, iasoql_endpoint_id: str):
        self.api_key = runpod_api_key
        self.endpoint_id = iasoql_endpoint_id
        self.base_url = f"https://api.runpod.ai/v2/{iasoql_endpoint_id}"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Common query templates
        self.templates = {
            # Patient queries
            "count_patients_by_condition": {
                "pattern": r"(count|how many) patients? (have|with) (\w+)",
                "sql": """
                    SELECT COUNT(DISTINCT JSONExtractString(resource, '$.subject.reference')) as patient_count
                    FROM nexuscare_analytics.fhir_current
                    WHERE tenant_id = '{tenant_id}'
                    AND sign = 1
                    AND resource_type = 'Condition'
                    AND JSONExtractString(resource, '$.code.coding[0].display') ILIKE '%{condition}%'
                """
            },
            
            # Lab result queries
            "recent_lab_results": {
                "pattern": r"(recent|latest) lab (results?|tests?) for patient (\w+)",
                "sql": """
                    SELECT 
                        JSONExtractString(resource, '$.code.display') as test_name,
                        JSONExtractFloat(resource, '$.valueQuantity.value') as value,
                        JSONExtractString(resource, '$.valueQuantity.unit') as unit,
                        JSONExtractString(resource, '$.effectiveDateTime') as test_date,
                        JSONExtractString(resource, '$.interpretation[0].text') as interpretation
                    FROM nexuscare_analytics.fhir_current
                    WHERE tenant_id = '{tenant_id}'
                    AND sign = 1
                    AND resource_type = 'Observation'
                    AND JSONExtractString(resource, '$.subject.reference') = 'Patient/{patient_id}'
                    ORDER BY parseDateTimeBestEffort(JSONExtractString(resource, '$.effectiveDateTime')) DESC
                    LIMIT 20
                """
            },
            
            # Medication queries
            "active_medications": {
                "pattern": r"(active|current) medications? for patient (\w+)",
                "sql": """
                    SELECT 
                        JSONExtractString(resource, '$.medicationCodeableConcept.coding[0].display') as medication,
                        JSONExtractString(resource, '$.dosageInstruction[0].text') as dosage,
                        JSONExtractString(resource, '$.authoredOn') as prescribed_date,
                        JSONExtractString(resource, '$.status') as status
                    FROM nexuscare_analytics.fhir_current
                    WHERE tenant_id = '{tenant_id}'
                    AND sign = 1
                    AND resource_type = 'MedicationRequest'
                    AND JSONExtractString(resource, '$.subject.reference') = 'Patient/{patient_id}'
                    AND JSONExtractString(resource, '$.status') = 'active'
                    ORDER BY parseDateTimeBestEffort(JSONExtractString(resource, '$.authoredOn')) DESC
                """
            },
            
            # Appointment queries
            "upcoming_appointments": {
                "pattern": r"(upcoming|next|future) appointments?",
                "sql": """
                    SELECT 
                        JSONExtractString(resource, '$.description') as description,
                        JSONExtractString(resource, '$.start') as appointment_time,
                        JSONExtractString(resource, '$.participant[0].actor.display') as provider,
                        JSONExtractString(resource, '$.status') as status
                    FROM nexuscare_analytics.fhir_current
                    WHERE tenant_id = '{tenant_id}'
                    AND sign = 1
                    AND resource_type = 'Appointment'
                    AND parseDateTimeBestEffort(JSONExtractString(resource, '$.start')) > now()
                    ORDER BY parseDateTimeBestEffort(JSONExtractString(resource, '$.start')) ASC
                    LIMIT 10
                """
            },
            
            # Vital signs
            "recent_vitals": {
                "pattern": r"(recent|latest) vital signs? for patient (\w+)",
                "sql": """
                    SELECT 
                        JSONExtractString(resource, '$.code.coding[0].display') as vital_type,
                        JSONExtractFloat(resource, '$.valueQuantity.value') as value,
                        JSONExtractString(resource, '$.valueQuantity.unit') as unit,
                        JSONExtractString(resource, '$.effectiveDateTime') as recorded_date
                    FROM nexuscare_analytics.fhir_current
                    WHERE tenant_id = '{tenant_id}'
                    AND sign = 1
                    AND resource_type = 'Observation'
                    AND JSONExtractString(resource, '$.subject.reference') = 'Patient/{patient_id}'
                    AND JSONExtractString(resource, '$.category[0].coding[0].code') = 'vital-signs'
                    ORDER BY parseDateTimeBestEffort(JSONExtractString(resource, '$.effectiveDateTime')) DESC
                    LIMIT 10
                """
            }
        }
    
    def find_template_match(self, query: str) -> Optional[Dict[str, Any]]:
        """Find matching template for the query"""
        query_lower = query.lower().strip()
        
        for template_name, template_data in self.templates.items():
            pattern = template_data["pattern"]
            match = re.search(pattern, query_lower)
            if match:
                return {
                    "template_name": template_name,
                    "template": template_data,
                    "match_groups": match.groups()
                }
        
        return None
    
    async def generate_sql_with_template(
        self, 
        query: str, 
        tenant_id: str = "demo_tenant",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Try template first, fall back to LLM if needed"""
        
        # Try to match a template
        template_match = self.find_template_match(query)
        
        if template_match:
            logger.info(f"Found template match: {template_match['template_name']}")
            
            # Extract parameters from query
            sql_template = template_match["template"]["sql"]
            match_groups = template_match["match_groups"]
            
            # Build parameters
            params = {"tenant_id": tenant_id}
            
            # Template-specific parameter extraction
            if "patient" in query.lower():
                # Extract patient ID
                patient_match = re.search(r'patient[:\s]+(\w+)', query.lower())
                if patient_match:
                    params["patient_id"] = patient_match.group(1)
            
            if "condition" in template_match["template_name"]:
                # Extract condition name
                if len(match_groups) >= 3:
                    params["condition"] = match_groups[2]
            
            # Format SQL with parameters
            try:
                sql = sql_template.format(**params)
                return {
                    "sql": sql,
                    "source": "template",
                    "template_name": template_match["template_name"],
                    "confidence": "high"
                }
            except KeyError as e:
                logger.warning(f"Template parameter missing: {e}")
                # Fall through to LLM
        
        # No template match or template failed - use IASOQL LLM
        return await self.generate_sql_with_llm(query, context)
    
    async def generate_sql_with_llm(
        self, 
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate SQL using IASOQL LLM on RunPod"""
        
        # Prepare request
        payload = {
            "input": {
                "query": query,
                "schema_context": self._get_schema_context(),
                "rag_context": context.get("rag_context", "") if context else "",
                "examples": self._get_few_shot_examples()
            }
        }
        
        # Call RunPod endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/runsync",
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"RunPod API error: {response.text}")
            
            result = response.json()
            
            if result.get("status") == "COMPLETED":
                output = result.get("output", {})
                return {
                    "sql": output.get("sql"),
                    "source": "llm",
                    "confidence": "medium",
                    "metadata": output.get("metadata", {})
                }
            else:
                raise Exception(f"IASOQL generation failed: {result}")
    
    def _get_schema_context(self) -> str:
        """Get ClickHouse schema context"""
        return """
Database: nexuscare_analytics
Table: fhir_current

Columns:
- tenant_id: String (tenant identifier)
- resource_type: String (FHIR resource type: Patient, Observation, Condition, etc.)
- resource_id: String (unique resource ID)
- resource: JSON (full FHIR resource as JSON)
- sign: Int8 (1 = current version, -1 = deleted)
- version_id: String
- created_at: DateTime

Common FHIR Resource Types:
- Patient: Demographics and patient information
- Observation: Lab results, vital signs, measurements
- Condition: Diagnoses and health conditions
- MedicationRequest: Prescriptions and medication orders
- Appointment: Scheduled appointments
- Encounter: Clinical visits and admissions
- Procedure: Medical procedures performed
- AllergyIntolerance: Patient allergies

JSON Path Examples:
- Patient name: $.name[0].given[0] + $.name[0].family
- Observation value: $.valueQuantity.value
- Condition code: $.code.coding[0].code
- Medication name: $.medicationCodeableConcept.coding[0].display
"""
    
    def _get_few_shot_examples(self) -> List[Dict[str, str]]:
        """Get few-shot examples for IASOQL"""
        return [
            {
                "query": "Find all patients with diabetes diagnosed this year",
                "sql": """SELECT DISTINCT JSONExtractString(resource, '$.subject.reference') as patient_id,
       JSONExtractString(resource, '$.code.coding[0].display') as condition,
       JSONExtractString(resource, '$.recordedDate') as diagnosis_date
FROM nexuscare_analytics.fhir_current
WHERE tenant_id = 'demo_tenant'
  AND sign = 1
  AND resource_type = 'Condition'
  AND (JSONExtractString(resource, '$.code.coding[0].code') LIKE 'E11%'
       OR JSONExtractString(resource, '$.code.coding[0].display') ILIKE '%diabetes%')
  AND toYear(parseDateTimeBestEffort(JSONExtractString(resource, '$.recordedDate'))) = toYear(now())"""
            },
            {
                "query": "Show lab results above normal range for patient 123",
                "sql": """SELECT JSONExtractString(resource, '$.code.display') as test_name,
       JSONExtractFloat(resource, '$.valueQuantity.value') as value,
       JSONExtractString(resource, '$.valueQuantity.unit') as unit,
       JSONExtractFloat(resource, '$.referenceRange[0].high.value') as upper_limit,
       JSONExtractString(resource, '$.interpretation[0].coding[0].code') as interpretation
FROM nexuscare_analytics.fhir_current
WHERE tenant_id = 'demo_tenant'
  AND sign = 1
  AND resource_type = 'Observation'
  AND JSONExtractString(resource, '$.subject.reference') = 'Patient/123'
  AND JSONExtractString(resource, '$.interpretation[0].coding[0].code') IN ('H', 'HH', 'HU')
ORDER BY parseDateTimeBestEffort(JSONExtractString(resource, '$.effectiveDateTime')) DESC"""
            }
        ]
    
    # MCP Tool definitions
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return MCP tool definitions"""
        return [
            {
                "name": "generate_healthcare_sql",
                "description": "Generate ClickHouse SQL for healthcare analytics queries. Uses templates for common queries and IASOQL LLM for complex queries.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query about healthcare data"
                        },
                        "tenant_id": {
                            "type": "string",
                            "description": "Tenant ID for multi-tenant data isolation",
                            "default": "demo_tenant"
                        },
                        "use_rag_context": {
                            "type": "boolean",
                            "description": "Whether to include RAG context for better SQL generation",
                            "default": True
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "validate_healthcare_sql",
                "description": "Validate generated SQL for safety and correctness",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL query to validate"
                        }
                    },
                    "required": ["sql"]
                }
            }
        ]