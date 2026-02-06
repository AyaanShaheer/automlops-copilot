from typing import Dict
from loguru import logger
from src.llm.llm_client import LLMClient

class FastAPIGenerator:
    """Generates FastAPI inference service"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def generate(self, repo_analysis: Dict) -> str:
        """Generate FastAPI service for model inference"""
        
        frameworks = repo_analysis.get("ml_frameworks", [])
        
        system_prompt = """You are an expert in building production ML APIs. Generate a FastAPI application that:
- Loads the trained model from disk
- Provides a /predict endpoint
- Includes health check endpoint
- Has proper request/response models with Pydantic
- Handles errors gracefully
- Includes CORS middleware
- Has proper logging

Output ONLY the Python code for app.py, no explanations."""

        user_prompt = f"""Generate a FastAPI inference service for this ML model:

**ML Frameworks**: {', '.join(frameworks) if frameworks else 'scikit-learn'}

**Requirements**:
1. Load model from file (model.pkl or model.pth or model.h5)
2. POST /predict endpoint accepting JSON data
3. GET /health endpoint
4. GET / endpoint with API info
5. Proper error handling
6. Input validation with Pydantic

Generate the app.py file:"""

        try:
            api_content = self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=3072
            )
            
            api_content = self._clean_code(api_content)
            logger.success("FastAPI service generated successfully")
            return api_content
            
        except Exception as e:
            logger.error(f"Failed to generate FastAPI service: {e}")
            return self._generate_fallback_fastapi()
    
    def _clean_code(self, content: str) -> str:
        """Clean up generated code"""
        if "```python" in content:
            content = content.split("```python")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```").split("```")[1]
        
        return content.strip()
    
    def _generate_fallback_fastapi(self) -> str:
        """Generate fallback FastAPI service"""
        return """from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np
from typing import List, Any
import os

app = FastAPI(title="AutoMLOps Inference API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model
MODEL_PATH = os.getenv("MODEL_PATH", "model.pkl")
model = None

@app.on_event("startup")
async def load_model():
    global model
    try:
        model = joblib.load(MODEL_PATH)
        print(f"Model loaded from {MODEL_PATH}")
    except Exception as e:
        print(f"Failed to load model: {e}")

class PredictRequest(BaseModel):
    data: List[List[float]]

class PredictResponse(BaseModel):
    predictions: List[Any]

@app.get("/")
async def root():
    return {
        "message": "AutoMLOps Inference API",
        "status": "running",
        "model_loaded": model is not None
    }

@app.get("/health")
async def health():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy"}

@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        data = np.array(request.data)
        predictions = model.predict(data)
        return {"predictions": predictions.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""
