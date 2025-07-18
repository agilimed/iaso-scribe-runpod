# Clinical AI Migration Checklist

## Pre-Migration Tasks

### 1. Clean Sensitive Data
- [ ] Remove `.env` file (create `.env.example` instead)
- [ ] Remove any API keys, passwords, or credentials
- [ ] Check for hardcoded secrets in Python files
- [ ] Remove or gitignore trained MedCAT models (they can be large)

### 2. Prepare Directory Structure
```
clinical-ai/
├── services/
│   ├── clinical-ai/      # From clinicalai_service/
│   ├── terminology/      # From terminology_service/
│   ├── knowledge/        # From knowledge_service/
│   ├── template/         # From template_service/
│   └── slm/             # From slm_service/
├── infrastructure/
│   ├── docker-compose.yml
│   └── kubernetes/      # K8s manifests
├── docs/
├── scripts/
└── README.md
```

### 3. Update Configurations
- [ ] Update import paths to reflect new structure
- [ ] Update docker-compose.yml service names and paths
- [ ] Update API URLs in configuration files
- [ ] Merge requirements.txt with existing one

### 4. Integration Points
- [ ] Update CLAUDE.md with clinical AI services
- [ ] Add clinical AI endpoints to insights-ai/api_gateway.py
- [ ] Create unified authentication mechanism
- [ ] Ensure service discovery works

## Migration Steps

### Step 1: Backup Current State
```bash
# Create backup of nexus-care-ai-backend
cp -r ../nexus-care-ai-backend ../nexus-care-ai-backend.backup
```

### Step 2: Clean Sensitive Data
```bash
# In nexus-care-ai-backend directory
cd ../nexus-care-ai-backend
rm -f .env
cp .env .env.example  # If you want to keep template
# Edit .env.example to remove actual values

# Remove large model files
find . -name "*.pkl" -size +100M -delete
find . -name "*.dat" -size +100M -delete
```

### Step 3: Perform Migration (Choose One)

#### Option A: Using Git Subtree (Recommended)
```bash
cd /Users/vivkris/dev_projects/nexuscare-ai
git subtree add --prefix=clinical-ai ../nexus-care-ai-backend main --squash
```

#### Option B: Using rsync
```bash
cd /Users/vivkris/dev_projects/nexuscare-ai
mkdir -p clinical-ai

rsync -av \
  --exclude='.git' \
  --exclude='.env' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='logs' \
  --exclude='*.log' \
  --exclude='backup' \
  ../nexus-care-ai-backend/ ./clinical-ai/
```

### Step 4: Post-Migration Tasks
- [ ] Create clinical-ai/.env.example from template
- [ ] Update clinical-ai/README.md with integration instructions
- [ ] Test each service can start independently
- [ ] Update main README.md to include clinical AI services
- [ ] Create GitHub Actions for clinical AI CI/CD

## Service-Specific Considerations

### MedCAT Models
- Store trained models in Google Cloud Storage
- Download during deployment (not in git)
- Document model training process

### Database Migrations
- PostgreSQL schemas need to be migrated
- Redis/KeyDB data structures documented
- MeiliSearch indexes need recreation

### Dependencies
- Merge Python requirements
- Check for version conflicts
- Consider using Poetry for better dependency management

## Testing Plan
1. Unit tests for each service
2. Integration tests between services
3. End-to-end clinical workflow tests
4. Performance benchmarks with MedCAT

## Rollback Plan
If migration fails:
1. Delete clinical-ai/ directory
2. Restore from backup
3. Document issues encountered