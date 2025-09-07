from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class EmotionMetrics(BaseModel):
    valence: float = Field(..., ge=-1.0, le=1.0)
    arousal: float = Field(..., ge=0.0, le=1.0)
    primary_emotions: List[str] = Field(default_factory=list, max_length=3)
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str

    @field_validator("primary_emotions", mode="before")
    @classmethod
    def clamp_len(cls, v):
        return (v or [])[:3]

class EvalScores(BaseModel):
    empathy: float = Field(..., ge=0.0, le=1.0)
    specificity: float = Field(..., ge=0.0, le=1.0)
    safety: float = Field(..., ge=0.0, le=1.0)
    revise: bool
    critique: str = ""

class SafetyLabel(BaseModel):
    is_critical: bool
    category: Optional[str] = None       # e.g., self-harm, violence, medical, etc.
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = ""
    crisis_message: Optional[str] = None
