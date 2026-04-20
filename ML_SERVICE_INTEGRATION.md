# ML Service Integration Guide - Depression Prediction

## Overview

This document describes the integration of the depression prediction model from the Jupyter notebook into the MHealth platform. The system uses a Random Forest model trained on TSFEL-extracted audio features to predict depression risk from call recordings.

## Architecture

```
Twilio Call Recording
         ↓
   Twilio Webhook
         ↓
   TwilioResponses stored in DB
         ↓
   Call Completed
         ↓ 
   _trigger_depression_analysis()
         ↓
   Celery Task: analyze_call_depression_risk
         ↓
   ML Service: /api/ml/depression
         ↓
   Random Forest Prediction
         ↓
   Store in TwilioCalls table (Depression_Risk, Depression_Risk_Probability, etc)
         ↓
   Frontend displays depression risk on Call Management page
```

## Changes Made

### 1. ML Service (`ml-service/`)

#### Updated Files:
- **requirements.txt** - Added `tsfel` dependency
- **app/config.py** - Added depression model configuration and threshold
- **app/main.py** - Added depression prediction endpoints

#### New Files:
- **app/services/depression_prediction.py** - DepressionPredictionService class

#### Key Endpoints:
```
POST /api/ml/depression - Single audio file depression prediction
POST /api/ml/depression-batch - Multiple audio files
GET /health - Health check (includes depression service status)
```

### 2. Twilio Service (`twilio_service/`)

#### Updated Files:
- **app/models.py** - Added depression risk columns to TwilioCalls:
  - `Depression_Risk` (Integer: 0 or 1)
  - `Depression_Risk_Probability` (Float: 0.0-1.0)
  - `Depression_Risk_Level` (String: "High" or "Low")
  - `Depression_Risk_Confidence` (Float)
  - `Depression_Analysis_Timestamp` (DateTime)

- **app/schemas.py** - Updated `TwilioCallOut` to include depression fields

- **app/ml_client.py** - New ML Service client

- **alembic/versions/** - New migration `0004_add_depression_risk.py`

### 3. Frontend (`frontend2/`)

The API response now includes depression risk fields which can be displayed on the TwilioCallManagementPage.

## Setup Instructions

### 1. Install ML Service Dependencies

```bash
cd ml-service
pip install -r requirements.txt
```

### 2. Train Depression Model (One-Time Setup)

Use the provided `depression-prediction.ipynb` notebook. This generates:
- `model_store/random_forest_model.pkl` - Trained Random Forest model

Place this file in `ml-service/model_store/`

### 3. Apply Database Migration

```bash
cd twilio_service
alembic upgrade head
```

### 4. Configure Environment Variables

Add to `.env` (both twilio_service and ml-service):

```bash
# ML Service Configuration
ML_SERVICE_URL=http://localhost:8001

# Depression Model Path (ML service)
DEPRESSION_MODEL_PATH=./model_store/random_forest_model.pkl
SEGMENT_DURATION=8.0  # 8-second audio segments
DEPRESSION_THRESHOLD=0.5  # Probability threshold for depression classification

# Target sample rate for depression model
TARGET_SAMPLE_RATE=16000
```

### 5. Start ML Service

```bash
cd ml-service
python start.ps1  # Windows
# or
./start.sh  # Linux/Mac
```

Verify it's running: `http://localhost:8001/health`

### 6. Update Twilio Service

The depression analysis is triggered automatically after a call completes. You must add a Celery task:

Create or update `/twilio_service/app/celery_config_twilio.py` to include:

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_call_depression_risk(self, call_id: str):
    """Analyze call recordings for depression risk using ML Service."""
    from app.ml_client import get_client as get_ml_client
    from app.sql_db import SessionLocal
    from app.models import TwilioCalls
    from datetime import datetime, timezone
    import logging
    
    logger = logging.getLogger(__name__)
    db = SessionLocal()
    
    try:
        call = db.query(TwilioCalls).filter(
            TwilioCalls.Call_Id == call_id
        ).first()
        
        if not call:
            logger.error(f"Call {call_id} not found")
            return
        
        # Get all recordings from this call
        recordings = [
            r.TwilioRecordingUrl 
            for r in call.responses 
            if r.TwilioRecordingUrl
        ]
        
        if not recordings:
            logger.warning(f"No recordings found for call {call_id}")
            return
        
        # Get ML Service client and make prediction
        ml_client = get_ml_client()
        
        # Use first recording for depression analysis
        # (or combine all recordings for comprehensive analysis)
        result = ml_client.predict_depression_from_url(
            recordings[0],
            threshold=DEPRESSION_THRESHOLD
        )
        
        if result and result.get("status") == "success":
            data = result["data"]
            call.Depression_Risk = data.get("depression_risk")
            call.Depression_Risk_Probability = data.get("risk_probability")
            call.Depression_Risk_Level = data.get("risk_level")
            call.Depression_Risk_Confidence = data.get("confidence")
            call.Depression_Analysis_Timestamp = datetime.now(timezone.utc)
            db.commit()
            logger.info(
                f"Depression analysis complete for call {call_id}: "
                f"{data['risk_level']} (prob: {data['risk_probability']:.2f})"
            )
        else:
            logger.error(f"Depression prediction failed for call {call_id}")
            
    except Exception as e:
        logger.error(f"Error in depression analysis: {e}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e)
    finally:
        db.close()
```

### 7. Trigger Depression Analysis from Webhook

Add to the `voice_respond` webhook in `main.py` (after call.Status = "Completed"):

```python
if is_last_question(question_index):
    if call:
        call.Status = "Completed"
        call.Ended_Time = datetime.now(timezone.utc)
        db.commit()
        _trigger_depression_analysis(str(call.Call_Id))  # NEW LINE
        _trigger_call_recording_archival(str(call.Call_Id))
    return Response(content=_build_closing_twiml(), media_type="text/xml")
```

Add helper function to main.py:

```python
def _trigger_depression_analysis(call_id: str):
    """Dispatch Celery task to analyze call recordings for depression risk."""
    from app.celery_config_twilio import analyze_call_depression_risk
    
    logger.info("Triggering depression analysis for call %s", call_id)
    result = analyze_call_depression_risk.delay(call_id=call_id)
    logger.info("Depression analysis task queued with task_id=%s", result.id)
```

## Model Details

### Features Used
- **TSFEL Features**: 156 acoustic/temporal features per segment
- **Segments**: 8-second audio segments with padding
- **Aggregation**: Mean, std, min, max across all segments → 624 total features
- **Classifier**: Random Forest (200 trees, max_depth=10)

### Output
- **Depression Risk**: Binary classification (0 = Non-depressed, 1 = Depressed)
- **Probability**: Probability of depression (0.0-1.0)
- **Confidence**: Max(probability, 1-probability)

### Threshold
- Default: 0.5 (can be adjusted via `DEPRESSION_THRESHOLD` env var)
- `probability >= threshold` → Depression Risk = 1

## Model Training

To retrain the model with new data:

```bash
python depression-prediction.ipynb
# Generates: model_store/random_forest_model.pkl
```

Commit the new model to the repository and deploy to `ml-service/model_store/`

## Testing

### 1. Test ML Service Endpoint

```bash
curl -X POST "http://localhost:8001/api/ml/depression" \
  -F "file=@/path/to/audio.wav"
```

### 2. Test Health Check

```bash
curl http://localhost:8001/health
```

### 3. Test Complete Flow

1. Make a call via admin API: `POST /calls/initiate`
2. Respond to all questions
3. Check after ~60 seconds: `GET /calls/{call_id}`
4. Verify `depression_risk_level` is populated

## Monitoring

### Logs
- ML Service: `ml-service/logs/`
- Twilio Service: `twilio_service/logs/` (check Celery task execution)
- Check Celery task status: `celery -A app.celery_config_twilio inspect active`

### Metrics to Monitor
- Prediction latency: Should be < 30 seconds per call
- Success rate: Should be > 95%
- Model accuracy: Compare with training set (see notebook for baseline metrics)

## Troubleshooting

### ML Service not responding
```bash
curl http://localhost:8001/health
# Should return status=healthy
```

### Depression analysis not triggered
- Check Celery worker is running
- Check logs for `_trigger_depression_analysis`
- Verify `ML_SERVICE_URL` is correct

### Model file not found
- Ensure `random_forest_model.pkl` exists in `ml-service/model_store/`
- Check `DEPRESSION_MODEL_PATH` env var points to correct location

### Low prediction scores
- Verify audio quality in recordings
- Check sample rate matches (should be 16000 Hz)
- Re-train model with more data if needed

## Future Enhancements

1. **Batch Processing**: Process multiple calls' recordings together
2. **Explainability**: Add feature importance analysis
3. **Confidence Intervals**: Provide uncertainty estimates
4. **Longitudinal Analysis**: Track depression risk over multiple calls
5. **Model Updates**: Periodic retraining with new call data
