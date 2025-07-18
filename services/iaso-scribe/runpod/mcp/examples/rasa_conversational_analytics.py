#!/usr/bin/env python3
"""
Example: Using RASA MCP with Conversational Analytics
Shows how RASA can enhance the insights engine with dialog management
"""

import asyncio
import json
from typing import Dict, Any, List

# Simulating the integration between RASA MCP and Conversational Analytics

class ConversationalAnalyticsWithRASA:
    """
    Integration example showing how RASA enhances conversational analytics
    """
    
    def __init__(self):
        self.rasa_endpoint = "http://localhost:8091"  # RASA MCP Server
        self.analytics_endpoint = "http://localhost:8080"  # Conversational Analytics
    
    async def analyze_patient_query_with_dialog(self, query: str) -> Dict[str, Any]:
        """
        Process a patient query using RASA for better understanding
        before generating SQL insights
        """
        
        print(f"\n=== Analyzing Query with RASA Dialog Management ===")
        print(f"Original Query: {query}")
        
        # Step 1: Extract entities and intent using RASA
        entities = await self.extract_medical_context(query)
        print(f"\nExtracted Medical Context:")
        print(f"- Intent: {entities['intent']['name']} (confidence: {entities['intent']['confidence']})")
        print(f"- Entities: {json.dumps(entities['entities'], indent=2)}")
        
        # Step 2: Enhance query with extracted context
        enhanced_query = await self.enhance_query_with_context(query, entities)
        print(f"\nEnhanced Query: {enhanced_query}")
        
        # Step 3: Generate SQL with enhanced context
        sql_result = await self.generate_insights_sql(enhanced_query, entities)
        print(f"\nGenerated SQL:")
        print(sql_result['sql'])
        
        # Step 4: Analyze conversation for additional insights
        conversation_insights = await self.analyze_conversation_pattern(query, entities)
        print(f"\nConversation Insights:")
        print(f"- Query Type: {conversation_insights['query_type']}")
        print(f"- Recommended Follow-ups: {conversation_insights['follow_ups']}")
        
        return {
            "original_query": query,
            "medical_context": entities,
            "enhanced_query": enhanced_query,
            "sql_result": sql_result,
            "conversation_insights": conversation_insights
        }
    
    async def extract_medical_context(self, text: str) -> Dict[str, Any]:
        """Use RASA to extract medical entities and intent"""
        
        # Simulate RASA MCP call
        return {
            "intent": {
                "name": "query_patient_labs",
                "confidence": 0.92
            },
            "entities": {
                "condition": ["diabetes", "hypertension"],
                "test_type": ["HbA1c", "glucose"],
                "time_reference": ["last month"],
                "severity": ["uncontrolled"]
            }
        }
    
    async def enhance_query_with_context(self, query: str, context: Dict[str, Any]) -> str:
        """Enhance the query with extracted medical context"""
        
        # Build enhanced query based on entities
        entities = context['entities']
        
        enhanced_parts = []
        
        # Add condition context
        if entities.get('condition'):
            enhanced_parts.append(f"for patients with {' and '.join(entities['condition'])}")
        
        # Add test type specifics
        if entities.get('test_type'):
            enhanced_parts.append(f"specifically {' and '.join(entities['test_type'])} tests")
        
        # Add temporal context
        if entities.get('time_reference'):
            enhanced_parts.append(f"from {entities['time_reference'][0]}")
        
        # Add severity context
        if entities.get('severity'):
            enhanced_parts.append(f"with {entities['severity'][0]} values")
        
        enhanced = f"{query} {' '.join(enhanced_parts)}"
        return enhanced
    
    async def generate_insights_sql(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL using conversational analytics with RASA context"""
        
        # Based on RASA intent, choose appropriate SQL template
        intent = context['intent']['name']
        entities = context['entities']
        
        sql_templates = {
            "query_patient_labs": """
                WITH diabetic_patients AS (
                    SELECT DISTINCT patient_id
                    FROM conditions
                    WHERE code IN ({condition_codes})
                ),
                recent_labs AS (
                    SELECT 
                        p.patient_id,
                        p.name,
                        o.code,
                        o.value,
                        o.unit,
                        o.date,
                        CASE 
                            WHEN o.code = '4548-4' AND o.value > 7.0 THEN 'Uncontrolled'
                            WHEN o.code = '2339-0' AND o.value > 180 THEN 'High'
                            ELSE 'Controlled'
                        END as control_status
                    FROM observations o
                    JOIN patients p ON o.patient_id = p.patient_id
                    WHERE o.patient_id IN (SELECT patient_id FROM diabetic_patients)
                        AND o.code IN ({lab_codes})
                        AND o.date >= CURRENT_DATE - INTERVAL '30 days'
                )
                SELECT 
                    patient_id,
                    name,
                    code as test_type,
                    value,
                    unit,
                    date,
                    control_status
                FROM recent_labs
                WHERE control_status = 'Uncontrolled'
                ORDER BY value DESC
            """,
            
            "medication_adherence": """
                SELECT 
                    p.patient_id,
                    p.name,
                    m.medication,
                    m.last_filled,
                    m.days_supply,
                    m.adherence_rate
                FROM patients p
                JOIN medication_adherence m ON p.patient_id = m.patient_id
                WHERE m.adherence_rate < 0.8
                ORDER BY m.adherence_rate
            """
        }
        
        # Map entities to codes
        condition_codes = self.map_conditions_to_codes(entities.get('condition', []))
        lab_codes = self.map_labs_to_codes(entities.get('test_type', []))
        
        sql = sql_templates.get(intent, "SELECT * FROM patients LIMIT 10")
        sql = sql.format(
            condition_codes=','.join(f"'{c}'" for c in condition_codes),
            lab_codes=','.join(f"'{c}'" for c in lab_codes)
        )
        
        return {
            "sql": sql,
            "intent_based": True,
            "entity_mappings": {
                "conditions": condition_codes,
                "labs": lab_codes
            }
        }
    
    async def analyze_conversation_pattern(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the conversation pattern for insights"""
        
        intent = context['intent']['name']
        
        # Define follow-up patterns based on intent
        follow_up_patterns = {
            "query_patient_labs": [
                "Would you like to see the trend over time?",
                "Should I include medication adherence data?",
                "Do you want to compare with control targets?"
            ],
            "medication_adherence": [
                "Would you like to see refill patterns?",
                "Should I check for drug interactions?",
                "Do you want to see cost analysis?"
            ]
        }
        
        # Determine query type
        query_types = {
            "query_patient_labs": "Clinical Monitoring",
            "medication_adherence": "Medication Management",
            "appointment_scheduling": "Care Coordination"
        }
        
        return {
            "query_type": query_types.get(intent, "General Query"),
            "follow_ups": follow_up_patterns.get(intent, ["Would you like more details?"]),
            "conversation_depth": 1,
            "requires_clinical_context": True
        }
    
    def map_conditions_to_codes(self, conditions: List[str]) -> List[str]:
        """Map condition names to ICD codes"""
        condition_map = {
            "diabetes": ["E11.9", "E10.9"],
            "hypertension": ["I10", "I11.9"],
            "heart disease": ["I25.9", "I50.9"]
        }
        
        codes = []
        for condition in conditions:
            codes.extend(condition_map.get(condition.lower(), []))
        
        return codes
    
    def map_labs_to_codes(self, labs: List[str]) -> List[str]:
        """Map lab names to LOINC codes"""
        lab_map = {
            "hba1c": "4548-4",
            "glucose": "2339-0",
            "cholesterol": "2093-3",
            "blood pressure": "55284-4"
        }
        
        codes = []
        for lab in labs:
            code = lab_map.get(lab.lower())
            if code:
                codes.append(code)
        
        return codes

async def demo_rasa_enhanced_analytics():
    """Demonstrate RASA-enhanced conversational analytics"""
    
    analytics = ConversationalAnalyticsWithRASA()
    
    # Example queries that benefit from RASA understanding
    queries = [
        "Show me patients with uncontrolled diabetes who had high glucose readings last month",
        "Which patients are not taking their blood pressure medications regularly?",
        "Find all diabetic patients who missed their recent HbA1c tests"
    ]
    
    for query in queries:
        result = await analytics.analyze_patient_query_with_dialog(query)
        print("\n" + "="*60 + "\n")

async def demo_multi_turn_conversation():
    """Demonstrate multi-turn conversation with context"""
    
    print("\n=== Multi-Turn Conversation Example ===\n")
    
    # Simulate a conversation about patient monitoring
    conversation = [
        {
            "user": "Show me diabetic patients",
            "context": "initial_query"
        },
        {
            "user": "Focus on those with recent high readings",
            "context": "refinement"
        },
        {
            "user": "Add their medication adherence",
            "context": "expansion"
        },
        {
            "user": "Generate a report for Dr. Smith",
            "context": "action"
        }
    ]
    
    # RASA maintains context across turns
    session_id = "conv_123"
    
    for turn in conversation:
        print(f"User: {turn['user']}")
        print(f"Context Type: {turn['context']}")
        
        # RASA would maintain the conversation state
        # and understand context from previous turns
        print("RASA: Understanding context from previous messages...")
        print("SQL: [Progressively refined based on conversation]\n")

async def demo_entity_extraction_for_analytics():
    """Show how RASA entity extraction improves analytics"""
    
    print("\n=== Entity Extraction for Better Analytics ===\n")
    
    # Complex medical query
    query = """
    I need to see all patients with severe hypertension who are on ACE inhibitors 
    but had elevated potassium levels in the past 3 months, especially those over 65
    """
    
    # RASA extracts structured information
    extracted = {
        "conditions": ["hypertension"],
        "severity": ["severe"],
        "medications": ["ACE inhibitors"],
        "lab_values": ["potassium"],
        "lab_status": ["elevated"],
        "time_frame": ["3 months"],
        "age_group": ["over 65"]
    }
    
    print(f"Original Query: {query}")
    print(f"\nRASA Extracted Entities:")
    for entity_type, values in extracted.items():
        print(f"  {entity_type}: {values}")
    
    print("\nThis structured extraction enables:")
    print("- More accurate SQL generation")
    print("- Better query understanding")
    print("- Relevant follow-up suggestions")
    print("- Context-aware responses")

async def main():
    """Run all demonstrations"""
    
    print("RASA MCP Integration with Conversational Analytics")
    print("=" * 60)
    
    # Run demos
    await demo_rasa_enhanced_analytics()
    await demo_multi_turn_conversation()
    await demo_entity_extraction_for_analytics()
    
    print("\n=== Benefits of RASA Integration ===")
    print("1. Better query understanding through intent recognition")
    print("2. Accurate entity extraction for medical concepts")
    print("3. Multi-turn conversation support with context")
    print("4. Structured data extraction for SQL generation")
    print("5. Conversation analysis for insights and patterns")

if __name__ == "__main__":
    asyncio.run(main())