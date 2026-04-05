from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Emotion Analysis
# ---------------------------------------------------------------------------

class EmotionMetrics(BaseModel):
    valence: float = Field(..., ge=-1.0, le=1.0)
    arousal: float = Field(..., ge=0.0, le=1.0)
    primary_emotions: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str

    @field_validator("primary_emotions", mode="before")
    @classmethod
    def clamp_len(cls, v):
        return (v or [])[:3]


# ---------------------------------------------------------------------------
# Coaching Quality Evaluation
# ---------------------------------------------------------------------------

class EvalScores(BaseModel):
    empathy: float = Field(..., ge=0.0, le=1.0)
    specificity: float = Field(..., ge=0.0, le=1.0)
    safety: float = Field(..., ge=0.0, le=1.0)
    revise: bool
    critique: str = ""


# ---------------------------------------------------------------------------
# Safety / Crisis Detection
# ---------------------------------------------------------------------------

class SafetyLabel(BaseModel):
    is_critical: bool
    category: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = ""
    crisis_message: Optional[str] = None


# ---------------------------------------------------------------------------
# User Profile — persistent personalization data
# ---------------------------------------------------------------------------

class UserProfile(BaseModel):
    user_id: str
    name: str = ""
    preferred_techniques: List[str] = Field(default_factory=list)
    known_triggers: List[str] = Field(default_factory=list)
    emotion_summary: str = ""          # Claude-generated running summary
    total_sessions: int = 0
    last_active: Optional[str] = None  # ISO datetime string


# ---------------------------------------------------------------------------
# Memory — per-session snapshot stored for retrieval
# ---------------------------------------------------------------------------

class MemoryEntry(BaseModel):
    user_id: str
    session_id: str
    primary_emotions: List[str] = Field(default_factory=list)
    valence: float = 0.0
    text_preview: str = ""            # first 80 chars of user message
    coaching_preview: str = ""        # first 80 chars of coaching given
    ts: Optional[str] = None          # ISO datetime string


# ---------------------------------------------------------------------------
# Pattern Insight — cross-session emotional pattern analysis
# ---------------------------------------------------------------------------

class PatternInsight(BaseModel):
    user_id: str
    patterns: List[str] = Field(default_factory=list)   # e.g. ["Monday anxiety"]
    triggers: List[str] = Field(default_factory=list)   # e.g. ["work deadlines"]
    trend: str = ""                   # "improving" | "declining" | "stable"
    recommendation: str = ""          # actionable long-term suggestion
    generated_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Journal Prompt — reflective question generated from current emotion
# ---------------------------------------------------------------------------

class JournalPrompt(BaseModel):
    prompt: str
    emotion_context: str = ""
    suggested_duration_minutes: int = 5
