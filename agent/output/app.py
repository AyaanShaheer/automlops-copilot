# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.externals import joblib
import logging
from logging.config import dictConfig
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# Logging configuration
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
})

# Initialize the FastAPI app
app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:8000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the model
try:
    model = joblib.load('model.pkl')
except Exception as e:
    logging.error(f"Failed to load model: {e}")
    raise HTTPException(status_code=500, detail="Failed to load model")

# Define the request and response models
class PredictionRequest(BaseModel):
    data: list[float]

class PredictionResponse(BaseModel):
    prediction: float

# Define the API endpoints
@app.get('/')
def read_root():
    return {'API': 'ML Inference Service'}

@app.get('/health')
def read_health():
    return {'status': 'healthy'}

@app.post('/predict', response_model=PredictionResponse)
def predict(request: PredictionRequest):
    try:
        prediction = model.predict([request.data])
        return {'prediction': prediction[0]}
    except Exception as e:
        logging.error(f"Failed to make prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to make prediction")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)