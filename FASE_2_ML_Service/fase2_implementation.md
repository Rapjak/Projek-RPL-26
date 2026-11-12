# FASE 2: FastAPI ML Service Integration

## Overview
FASE 2 integrates FastAPI ML classification service with Django backend for real-time garbage classification.

## Architecture
```
User Upload → Django API → FastAPI ML Service → Classification Result → Django Database
                ↓
            Local File Storage
```

## Tasks Completed

### Task 1: FastAPI Service Setup
**Objective**: Create standalone FastAPI service for ML classification

**Implementation**:
- Created `ml_service/` directory with FastAPI application
- Endpoints:
  - `GET /` - Service info and health
  - `GET /health` - Docker health check
  - `POST /classify` - Single image classification
  - `POST /batch-classify` - Batch image classification

**Files Created**:
- `ml_service/main.py` - FastAPI application with classification endpoints
- `ml_service/requirements.txt` - Python dependencies (FastAPI, uvicorn, Pillow)
- `ml_service/Dockerfile` - Docker container configuration

**Key Features**:
- Async request handling
- Image validation (JPEG, PNG, GIF, WebP)
- Error handling and logging
- Health check endpoint for Docker
- Runs on port 8001

**Code Structure**:
```python
# Classification endpoint
@app.post("/classify")
async def classify_image_endpoint(file: UploadFile):
    # Validate file type
    # Load image with PIL
    # Run classification (placeholder)
    # Return structured result
```

### Task 2: ML Classification Logic
**Objective**: Implement garbage classification with environmental impact data

**Implementation**:
For FASE 2, implemented deterministic classification based on image size as placeholder. Production will use trained CNN model (ResNet/EfficientNet).

**Classification Categories** (10 types):
1. Plastic - Recyclable
2. Paper - Recyclable
3. Organic - Compostable
4. Metal - Recyclable
5. Glass - Recyclable
6. Cardboard - Recyclable
7. Ceramics - Non-recyclable
8. Cloth - Recyclable
9. Electronic - E-waste
10. Battery - Hazardous waste

**Response Schema**:
```json
{
  "success": true,
  "data": {
    "class_name": "Plastic",
    "confidence_score": 0.85,
    "is_recyclable": true,
    "handling_instructions": "Clean and recycle in plastic bin",
    "environmental_impact": "Recycling plastic reduces landfill waste and ocean pollution"
  },
  "file_info": {
    "filename": "image.jpg",
    "content_type": "image/jpeg",
    "size": 245680
  }
}
```

**Placeholder Logic**:
```python
def classify_image(image: Image.Image) -> dict:
    # Convert to RGB
    # Calculate image characteristics
    # Deterministic classification (DEMO)
    # Map to recyclability and handling instructions
    # Return structured result
```

### Task 3: Django-FastAPI Integration
**Objective**: Connect Django backend to FastAPI ML service

**Implementation**:
Created `MLServiceClient` utility class for clean integration.

**Files Modified/Created**:
- `apps/utils/ml_client.py` - ML Service HTTP client
- `apps/classifications/views.py` - Updated to use ML client
- `.env.example` - Added ML service configuration

**ML Client Features**:
- Configurable endpoint via `FASTAPI_ENDPOINT` env var
- Configurable timeout via `ML_SERVICE_TIMEOUT` env var
- Health check before classification
- Graceful fallback when service unavailable
- Batch classification support
- Proper error handling and logging

**Client Usage**:
```python
from apps.utils.ml_client import MLServiceClient

ml_client = MLServiceClient()

# Health check
if ml_client.health_check():
    # Classify image
    result = ml_client.classify_image(image_path, mime_type)
else:
    # Use fallback classification
```

**Graceful Degradation**:
When ML service unavailable:
- Health check fails (5s timeout)
- Returns fallback result with `class_name: "Unknown"`
- User receives response explaining service unavailable
- No database errors or request failures

### Task 4: Classification View Updates
**Objective**: Integrate ML service into classification workflow

**Changes to `apps/classifications/views.py`**:
1. Import `MLServiceClient` instead of direct `requests`
2. Health check before classification attempt
3. Derive MIME type from file extension
4. Call ML service with proper error handling
5. Store ML result in database
6. Award points on successful classification

**Classification Flow**:
```
1. Validate upload exists and belongs to user
2. Initialize ML client
3. Get image file path from Upload.file.path
4. Derive MIME type from file extension
5. Check ML service health
6. If healthy: Call ML service
   If unhealthy: Use fallback result
7. Create ClassificationResult with ML data
8. Update upload status to 'completed'
9. Award 10 points to user
10. Log point transaction
11. Invalidate caches
12. Return classification result
```

**Error Handling**:
- Upload not found: 404 response
- File not found: 404 response  
- ML service error: 500 with error message
- Upload status set to 'failed' on error
- Error logged with full traceback

### Task 5: Docker Integration
**Objective**: Add ML service to docker-compose infrastructure

**Changes to `FASE_0_Infrastructure/docker-compose.yml`**:
Added `ml-service` container:
```yaml
ml-service:
  build:
    context: ../ml_service
    dockerfile: Dockerfile
  container_name: pilah_ml_service
  ports:
    - "8001:8001"
  networks:
    - pilah_network
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 10s
  depends_on:
    - postgres
    - redis
  restart: unless-stopped
```

**Health Check**:
- Uses `/health` endpoint
- 30s interval between checks
- 10s timeout per check
- 3 retries before marking unhealthy
- 10s start period for initialization

### Task 6: Environment Configuration
**Objective**: Configure ML service connection

**Added to `.env.example`**:
```bash
# FastAPI ML Service Configuration
FASTAPI_ENDPOINT=http://localhost:8001
ML_SERVICE_TIMEOUT=30
```

**Development**:
- Local: `http://localhost:8001`
- Docker: `http://ml-service:8001` (internal network)

**Timeout**:
- Default: 30 seconds per classification
- Configurable via environment variable

### Task 7: Testing
**Objective**: Verify ML service integration works correctly

**Test Results**:
- All 23 tests pass
- Classification test works with fallback when ML service unavailable
- Graceful degradation verified
- No database errors when ML service down

**Test Coverage**:
- ✅ Classification with authenticated user (fallback mode)
- ✅ Classification without authentication (401)
- ✅ Upload creation and retrieval
- ✅ User management (register, login, profile)
- ✅ Rewards system (earn, redeem, history)
- ✅ Education content

**Manual Testing**:
```bash
# Start ML service
cd ml_service
python main.py

# Test classification endpoint
curl -X POST "http://localhost:8001/classify" \
  -F "file=@test_image.jpg"

# Expected response
{
  "success": true,
  "data": {
    "class_name": "Plastic",
    "confidence_score": 0.85,
    ...
  }
}
```

## Technical Specifications

### ML Service API
**Base URL**: `http://localhost:8001`

**Endpoints**:

1. **GET /** - Service information
   - Response: Service name, version, status, device

2. **GET /health** - Health check
   - Response: `{"status": "healthy"}`

3. **POST /classify** - Classify single image
   - Request: `multipart/form-data` with `file` field
   - Accepts: JPEG, PNG, GIF, WebP
   - Response: Classification result with confidence score

4. **POST /batch-classify** - Classify multiple images
   - Request: `multipart/form-data` with multiple `files`
   - Response: Array of classification results

### Django Integration
**MLServiceClient Class**:
```python
class MLServiceClient:
    def __init__(base_url: Optional[str])
    def health_check() -> bool
    def classify_image(image_path: str, mime_type: str) -> Dict
    def batch_classify(image_paths: list) -> list
```

**Configuration**:
- Base URL from `FASTAPI_ENDPOINT` env var
- Timeout from `ML_SERVICE_TIMEOUT` env var
- Automatic health checks
- Graceful error handling

### Database Schema
No changes to database schema in FASE 2. Uses existing `ClassificationResult` model with fields:
- `class_name` - Classification type
- `confidence_score` - Model confidence (0-1)
- `is_recyclable` - Boolean recyclability
- `handling_instructions` - Text instructions
- `environmental_impact` - Text impact description

## Deployment

### Local Development
1. Start ML service:
```bash
cd ml_service
pip install -r requirements.txt
python main.py
# Runs on http://localhost:8001
```

2. Start Django:
```bash
python manage.py runserver
# Runs on http://localhost:8000
```

### Docker Deployment
```bash
cd FASE_0_Infrastructure
docker-compose up -d
```

Services:
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- FastAPI ML: `localhost:8001`
- Django API: `localhost:8000` (manual start)

### Environment Variables
```bash
# Copy example
cp .env.example .env

# Edit ML service endpoint
FASTAPI_ENDPOINT=http://ml-service:8001  # Docker
FASTAPI_ENDPOINT=http://localhost:8001   # Local
```

## Future Improvements (FASE 3+)

### ML Model Enhancements
1. **Train Production Model**:
   - Use ResNet-50 or EfficientNet-B0
   - Train on garbage classification dataset
   - Achieve >90% accuracy
   - Save model weights

2. **Model Loading**:
```python
import torch
import torchvision.models as models

# Load pre-trained model
model = models.resnet50(weights=None)
model.load_state_dict(torch.load('garbage_classifier.pth'))
model.eval()
```

3. **Inference Pipeline**:
```python
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def classify_image(image: Image.Image) -> dict:
    img_tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        outputs = model(img_tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, 1)
    
    class_name = CLASS_NAMES[predicted.item()]
    confidence_score = confidence.item()
    # Map to recyclability and instructions
    return result
```

### Performance Optimization
- Model quantization for faster inference
- GPU acceleration (CUDA)
- Batch processing optimization
- Caching of repeated classifications
- CDN for model weights

### Advanced Features
- Multi-object detection in single image
- Contamination detection
- Material composition analysis
- Recycling location recommendations
- Carbon footprint calculations

## Files Changed/Created

### New Files
```
ml_service/
  ├── main.py                    # FastAPI application
  ├── requirements.txt           # Python dependencies
  └── Dockerfile                 # Docker configuration

apps/utils/
  └── ml_client.py               # ML service HTTP client

.env.example                     # Environment configuration
```

### Modified Files
```
apps/classifications/views.py   # ML service integration
FASE_0_Infrastructure/
  └── docker-compose.yml         # Added ml-service container
```

## Testing Commands

### Run All Tests
```bash
python manage.py test --settings=config.settings_test
```

### Run Classification Tests Only
```bash
python manage.py test tests.test_classifications --settings=config.settings_test
```

### Manual ML Service Test
```bash
# Terminal 1: Start ML service
cd ml_service
python main.py

# Terminal 2: Test endpoint
curl -X POST "http://localhost:8001/classify" \
  -F "file=@media/uploads/sample.jpg"
```

## Summary

FASE 2 successfully integrates FastAPI ML classification service with Django backend:

✅ **FastAPI Service**: Standalone ML service with classification endpoints  
✅ **Classification Logic**: 10 garbage categories with recyclability data  
✅ **Django Integration**: Clean client library with graceful fallback  
✅ **Docker Support**: ML service in docker-compose infrastructure  
✅ **Error Handling**: Robust error handling and health checks  
✅ **Testing**: All 23 tests pass with fallback mode  
✅ **Documentation**: Comprehensive implementation guide  

**Next Phase**: Frontend React application (FASE 3) to consume Django API and display classification results.
