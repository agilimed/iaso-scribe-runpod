# IasoChat Content Configuration System

## Overview

This document outlines how IasoChat can be configured to provide specialty-specific resources, content, and responses for different medical use cases (maternity, cardiology, orthopedics, etc.).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    IasoChat Configuration System                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Specialty      │  │   Content       │  │  Response       │ │
│  │  Registry       │  │   Repository    │  │  Templates      │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                     │           │
│  ┌────────▼────────────────────▼─────────────────────▼────────┐ │
│  │              Configuration Engine                           │ │
│  └────────┬────────────────────┬─────────────────────┬────────┘ │
│           │                    │                     │           │
│  ┌────────▼────────┐  ┌───────▼────────┐  ┌────────▼────────┐ │
│  │ Context Builder │  │ Content Matcher │  │ Response Gen   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 1. Specialty Configuration Schema

### Base Configuration Structure

```yaml
# specialties/maternity.yaml
specialty:
  id: maternity
  name: Maternal & Prenatal Care
  description: Comprehensive support for pregnancy and postpartum care
  
  # Medical context
  medical_context:
    conditions:
      - pregnancy
      - gestational_diabetes
      - preeclampsia
      - postpartum_depression
    
    risk_factors:
      - advanced_maternal_age
      - multiple_pregnancy
      - previous_complications
    
    stages:
      - first_trimester
      - second_trimester
      - third_trimester
      - postpartum
  
  # Emotion mapping
  emotion_responses:
    anxious:
      priority_topics:
        - labor_preparation
        - pain_management
        - baby_health
      
      response_tone: "gentle, reassuring, informative"
      
    excited:
      priority_topics:
        - baby_development
        - preparation_tips
        - bonding
      
      response_tone: "enthusiastic, supportive, educational"
  
  # Resource library
  resources:
    videos:
      - id: breathing_labor
        title: "Breathing Techniques for Labor"
        url: "https://content.iaso.health/maternity/breathing-labor"
        tags: ["labor", "pain_management", "third_trimester"]
        duration: "10:30"
        
      - id: prenatal_yoga
        title: "Safe Prenatal Yoga Routine"
        url: "https://content.iaso.health/maternity/prenatal-yoga"
        tags: ["exercise", "wellness", "all_trimesters"]
        duration: "20:00"
    
    audio:
      - id: pregnancy_meditation
        title: "Calming Pregnancy Meditation"
        url: "https://content.iaso.health/maternity/meditation-1"
        tags: ["anxiety", "relaxation", "sleep"]
        duration: "15:00"
    
    articles:
      - id: nutrition_guide
        title: "Nutrition During Pregnancy"
        url: "https://content.iaso.health/maternity/nutrition"
        tags: ["diet", "health", "all_trimesters"]
        reading_time: "5 min"
    
    support_contacts:
      - type: "hotline"
        name: "24/7 Maternal Support Line"
        number: "1-800-MAT-HELP"
        availability: "24/7"
        
      - type: "support_group"
        name: "New Mothers Circle"
        schedule: "Tuesdays & Thursdays 2 PM"
        join_url: "https://support.iaso.health/new-mothers"
  
  # Escalation rules
  escalation_rules:
    emergency_keywords:
      - "bleeding"
      - "severe pain"
      - "can't feel baby"
      - "contractions" # (before 37 weeks)
    
    urgency_thresholds:
      pain_scale: 8
      anxiety_score: 0.9
      depression_indicators: 3
  
  # Conversation templates
  conversation_starters:
    - "How are you feeling today in your pregnancy journey?"
    - "Is there anything about your pregnancy that's been on your mind?"
    - "How has your energy been lately?"
```

### Cardiology Configuration

```yaml
# specialties/cardiology.yaml
specialty:
  id: cardiology
  name: Cardiovascular Care
  description: Support for heart health and cardiovascular conditions
  
  medical_context:
    conditions:
      - coronary_artery_disease
      - heart_failure
      - arrhythmia
      - hypertension
    
    risk_factors:
      - high_cholesterol
      - diabetes
      - smoking
      - family_history
    
    monitoring_params:
      - blood_pressure
      - heart_rate
      - weight
      - medication_adherence
  
  resources:
    videos:
      - id: heart_healthy_diet
        title: "Heart-Healthy Eating Guide"
        url: "https://content.iaso.health/cardio/diet"
        tags: ["nutrition", "cholesterol", "prevention"]
        
      - id: cardiac_rehab_exercises
        title: "Safe Exercises After Heart Surgery"
        url: "https://content.iaso.health/cardio/rehab"
        tags: ["recovery", "exercise", "post_surgery"]
    
    monitoring_tools:
      - id: bp_tracker
        title: "Blood Pressure Tracker"
        type: "interactive_tool"
        url: "https://tools.iaso.health/bp-tracker"
        
      - id: med_reminder
        title: "Medication Reminder Setup"
        type: "app_integration"
        deeplink: "iaso://med-reminder"
```

## 2. Dynamic Content Management System

### Content Repository Structure

```python
class ContentRepository:
    def __init__(self):
        self.specialties = {}
        self.content_index = ContentIndex()
        self.recommendation_engine = RecommendationEngine()
    
    def load_specialty(self, specialty_id: str):
        """Load specialty configuration from YAML/Database"""
        config_path = f"specialties/{specialty_id}.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Index content for fast retrieval
        self.content_index.index_specialty(specialty_id, config)
        
        # Train recommendation model
        self.recommendation_engine.train_specialty_model(
            specialty_id, 
            config['resources']
        )
        
        self.specialties[specialty_id] = config
        return config

    def get_relevant_content(self, context: dict) -> List[Resource]:
        """Get content based on context"""
        specialty = context['specialty']
        patient_stage = context.get('stage')
        emotions = context.get('emotions', [])
        symptoms = context.get('symptoms', [])
        
        # Build query
        query = ContentQuery(
            specialty=specialty,
            tags=symptoms + emotions + [patient_stage],
            limit=5
        )
        
        # Get recommendations
        return self.recommendation_engine.recommend(query)
```

### Content Recommendation Engine

```python
class RecommendationEngine:
    def __init__(self):
        self.embeddings_model = BGE_M3_Model()
        self.specialty_models = {}
    
    def train_specialty_model(self, specialty_id: str, resources: dict):
        """Train specialty-specific recommendation model"""
        # Create embeddings for all content
        content_embeddings = []
        
        for resource_type, items in resources.items():
            for item in items:
                embedding = self.embeddings_model.encode(
                    f"{item['title']} {' '.join(item.get('tags', []))}"
                )
                content_embeddings.append({
                    'id': item['id'],
                    'type': resource_type,
                    'embedding': embedding,
                    'metadata': item
                })
        
        # Store in vector database
        self.store_embeddings(specialty_id, content_embeddings)
    
    def recommend(self, query: ContentQuery) -> List[Resource]:
        """Get personalized recommendations"""
        # Encode query
        query_embedding = self.embeddings_model.encode(
            ' '.join(query.tags)
        )
        
        # Search in specialty-specific collection
        results = self.vector_db.search(
            collection=f"{query.specialty}_resources",
            query_vector=query_embedding,
            limit=query.limit,
            filter={
                'stage': query.stage,
                'resource_type': query.resource_types
            }
        )
        
        # Apply business rules
        return self.apply_recommendation_rules(results, query)
    
    def apply_recommendation_rules(self, results, query):
        """Apply specialty-specific rules"""
        # Example: For maternity, prioritize trimester-specific content
        if query.specialty == 'maternity' and query.stage:
            results = sorted(
                results, 
                key=lambda x: x['metadata'].get('stage') == query.stage,
                reverse=True
            )
        
        # Example: For cardiology, prioritize monitoring tools for recent discharge
        if query.specialty == 'cardiology' and 'post_discharge' in query.tags:
            monitoring_tools = [r for r in results if r['type'] == 'monitoring_tools']
            other_resources = [r for r in results if r['type'] != 'monitoring_tools']
            results = monitoring_tools[:2] + other_resources[:3]
        
        return results
```

## 3. Configuration API

### Specialty Management Endpoints

```python
# 1. Register/Update Specialty
PUT /api/v1/chat/specialties/{specialty_id}
{
  "name": "Orthopedic Care",
  "medical_context": {
    "conditions": ["arthritis", "fractures", "joint_replacement"],
    "recovery_stages": ["acute", "rehabilitation", "maintenance"]
  },
  "resources": {
    "videos": [...],
    "exercises": [...],
    "pain_management": [...]
  }
}

# 2. Add Resources to Specialty
POST /api/v1/chat/specialties/{specialty_id}/resources
{
  "type": "video",
  "resource": {
    "title": "Post-Surgery Knee Exercises",
    "url": "https://content.iaso.health/ortho/knee-exercises",
    "tags": ["knee", "post_surgery", "rehabilitation"],
    "restrictions": ["weight_bearing_allowed"]
  }
}

# 3. Configure Emotion Mappings
PUT /api/v1/chat/specialties/{specialty_id}/emotions
{
  "frustrated": {
    "response_tone": "understanding, practical, solution-focused",
    "priority_resources": ["pain_management", "recovery_timeline"],
    "escalation_threshold": 0.8
  }
}

# 4. Set Escalation Rules
PUT /api/v1/chat/specialties/{specialty_id}/escalation
{
  "rules": [
    {
      "condition": "keyword_match",
      "keywords": ["can't move", "numbness", "severe swelling"],
      "action": "immediate_provider_alert"
    },
    {
      "condition": "pain_score",
      "threshold": 9,
      "action": "urgent_callback"
    }
  ]
}
```

### Content Filtering and Personalization

```python
class ContentPersonalizer:
    def __init__(self):
        self.user_preferences = UserPreferencesDB()
        self.interaction_history = InteractionHistoryDB()
    
    def personalize_content(self, user_id: str, base_recommendations: List[Resource]):
        """Personalize content based on user history and preferences"""
        # Get user profile
        user_profile = self.user_preferences.get(user_id)
        history = self.interaction_history.get_recent(user_id, days=30)
        
        # Apply filters
        filtered = self.apply_user_filters(base_recommendations, user_profile)
        
        # Score based on interaction history
        scored = self.score_by_history(filtered, history)
        
        # Diversify content types
        diversified = self.diversify_content(scored)
        
        return diversified
    
    def apply_user_filters(self, resources, profile):
        """Apply user-specific filters"""
        filtered = resources
        
        # Language preference
        if profile.get('language') != 'en':
            filtered = [r for r in filtered if r.get('language') == profile['language']]
        
        # Accessibility needs
        if profile.get('needs_captions'):
            filtered = [r for r in filtered if r.get('has_captions', False)]
        
        # Cultural preferences
        if profile.get('cultural_preferences'):
            filtered = self.filter_by_cultural_sensitivity(filtered, profile['cultural_preferences'])
        
        return filtered
```

## 4. Multi-Tenant Configuration

### Organization-Level Customization

```python
class OrganizationConfig:
    """Allow healthcare organizations to customize content"""
    
    def __init__(self, org_id: str):
        self.org_id = org_id
        self.custom_resources = {}
        self.branding = {}
        self.policies = {}
    
    def add_custom_resource(self, specialty: str, resource: dict):
        """Add organization-specific resources"""
        # Example: Hospital's own educational videos
        resource['source'] = 'organization'
        resource['org_id'] = self.org_id
        
        if specialty not in self.custom_resources:
            self.custom_resources[specialty] = []
        
        self.custom_resources[specialty].append(resource)
    
    def set_content_policies(self, policies: dict):
        """Set organization-specific content policies"""
        self.policies = {
            'require_medical_review': True,
            'allowed_external_sources': ['mayo_clinic', 'cdc'],
            'prohibited_topics': policies.get('prohibited_topics', []),
            'mandatory_disclaimers': policies.get('disclaimers', {})
        }
```

### API Usage Example

```python
# Initialize chat with specialty context
POST /api/v1/chat/start
{
  "patient_id": "patient123",
  "specialty": "maternity",
  "organization_id": "hospital_xyz",
  "context": {
    "stage": "third_trimester",
    "week": 32,
    "conditions": ["gestational_diabetes"],
    "language": "es",
    "cultural_background": "hispanic"
  }
}

# Chat response with specialty-specific content
Response:
{
  "session_id": "chat456",
  "welcome_message": "¡Hola! Estoy aquí para apoyarte en tu tercer trimestre...",
  "initial_resources": [
    {
      "type": "video",
      "title": "Control de Diabetes Gestacional",
      "url": "https://content.iaso.health/maternity/es/diabetes-gestacional",
      "language": "es",
      "duration": "8:30"
    }
  ],
  "quick_actions": [
    "Revisar niveles de azúcar",
    "Contar movimientos del bebé",
    "Preparación para el parto"
  ]
}
```

## 5. Content Quality & Governance

### Medical Review Process

```python
class MedicalContentReview:
    def __init__(self):
        self.review_queue = ReviewQueue()
        self.medical_reviewers = MedicalReviewerPool()
    
    def submit_content(self, content: dict, specialty: str):
        """Submit content for medical review"""
        review_request = {
            'content': content,
            'specialty': specialty,
            'submitted_at': datetime.now(),
            'status': 'pending_review',
            'reviewer_requirements': {
                'specialty': specialty,
                'min_experience_years': 5
            }
        }
        
        # Auto-assign to qualified reviewer
        reviewer = self.medical_reviewers.assign_reviewer(review_request)
        
        return self.review_queue.add(review_request, reviewer)
    
    def review_content(self, review_id: str, reviewer_id: str, decision: dict):
        """Process medical review decision"""
        if decision['approved']:
            # Add medical review metadata
            content = self.review_queue.get(review_id)
            content['medical_review'] = {
                'reviewed_by': reviewer_id,
                'reviewed_at': datetime.now(),
                'validity_period': '1 year',
                'evidence_level': decision.get('evidence_level', 'expert_opinion')
            }
            
            # Publish to specialty
            self.publish_approved_content(content)
        else:
            # Send back for revision
            self.request_revision(review_id, decision['feedback'])
```

### Content Versioning & Updates

```python
class ContentVersionControl:
    def __init__(self):
        self.version_db = VersionDatabase()
    
    def update_content(self, content_id: str, updates: dict):
        """Version-controlled content updates"""
        # Get current version
        current = self.version_db.get_latest(content_id)
        
        # Create new version
        new_version = {
            'id': content_id,
            'version': current['version'] + 1,
            'changes': updates,
            'changed_by': updates['editor_id'],
            'changed_at': datetime.now(),
            'change_reason': updates['reason']
        }
        
        # Medical re-review required for significant changes
        if self.requires_medical_review(current, updates):
            new_version['status'] = 'pending_review'
        else:
            new_version['status'] = 'active'
        
        self.version_db.save(new_version)
        
        # Update all specialty references
        self.update_specialty_references(content_id, new_version)
```

## 6. Analytics & Optimization

### Content Performance Tracking

```python
class ContentAnalytics:
    def __init__(self):
        self.analytics_db = AnalyticsDatabase()
    
    def track_resource_interaction(self, interaction: dict):
        """Track how users interact with resources"""
        self.analytics_db.record({
            'user_id': interaction['user_id'],
            'resource_id': interaction['resource_id'],
            'specialty': interaction['specialty'],
            'interaction_type': interaction['type'],  # viewed, completed, shared
            'engagement_duration': interaction.get('duration'),
            'user_feedback': interaction.get('feedback'),
            'context': interaction['context']
        })
    
    def get_specialty_insights(self, specialty: str):
        """Get insights for content optimization"""
        return {
            'most_viewed': self.analytics_db.get_top_resources(specialty, 'views'),
            'highest_rated': self.analytics_db.get_top_resources(specialty, 'rating'),
            'completion_rates': self.analytics_db.get_completion_rates(specialty),
            'common_escalations': self.analytics_db.get_escalation_patterns(specialty),
            'underutilized_content': self.analytics_db.get_low_engagement_content(specialty)
        }
```

## 7. Implementation Example

### Complete Configuration for Orthopedics

```yaml
# specialties/orthopedics.yaml
specialty:
  id: orthopedics
  name: Orthopedic & Musculoskeletal Care
  
  medical_context:
    conditions:
      joint_conditions:
        - osteoarthritis
        - rheumatoid_arthritis
        - joint_replacement
      
      spine_conditions:
        - herniated_disc
        - spinal_stenosis
        - scoliosis
      
      trauma:
        - fractures
        - ligament_tears
        - tendon_injuries
    
    recovery_phases:
      - acute_post_surgery
      - early_rehabilitation  
      - strengthening
      - return_to_activity
  
  resources:
    exercise_programs:
      - id: knee_rehab_week1
        title: "Week 1-2 Post Knee Surgery"
        type: "interactive_guide"
        exercises:
          - name: "Quad Sets"
            reps: "10 x 3 daily"
            video_url: "..."
          - name: "Ankle Pumps"
            reps: "20 x 4 daily"
            video_url: "..."
        contraindications: ["infection", "unstable_hardware"]
    
    pain_management:
      - id: ice_therapy_guide
        title: "Proper Ice Therapy Technique"
        format: "infographic"
        key_points:
          - "20 minutes on, 40 minutes off"
          - "Never apply directly to skin"
          - "Elevation enhances effectiveness"
    
    recovery_tracking:
      - id: rom_tracker
        title: "Range of Motion Tracker"
        type: "mobile_app_integration"
        metrics:
          - knee_flexion_degrees
          - pain_level
          - swelling_assessment
```

This configuration system ensures that IasoChat can provide highly relevant, specialty-specific content while maintaining quality, safety, and personalization across all medical domains.