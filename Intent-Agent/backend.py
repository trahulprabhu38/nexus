# backend.py - FastAPI backend for Intent Agent
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from model_runner import extract_intent_payload
import uvicorn

app = FastAPI(title="Intent Agent API")

# Enable CORS for Streamlit UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": True}

class PredictRequest(BaseModel):
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    text: str
    metadata: Optional[Dict[str, Any]] = None

@app.post("/predict")
async def predict(req: PredictRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text field is required")
    
    # Call model runner
    try:
        payload = extract_intent_payload(req.text)
    except Exception as e:
        # Bubble errors as 500 with message
        raise HTTPException(status_code=500, detail=f"model error: {e}")

    # Attach passed-through ids
    if req.request_id:
        payload["request_id"] = req.request_id
    if req.session_id:
        payload["session_id"] = req.session_id
    if req.metadata:
        payload["metadata"] = req.metadata

    return payload

if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8080, reload=True)
