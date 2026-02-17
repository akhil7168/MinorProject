from pydantic import BaseModel
from typing import List

class PredictionRequest(BaseModel):
    features: List[float]

class PredictionResponse(BaseModel):
    is_attack: bool
    confidence: float
    label: str
