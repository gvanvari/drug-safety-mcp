from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Drug(BaseModel):
    """Reference drug data model"""
    id: int
    name: str
    category: str
    common_uses: List[str]
    fda_generic_name: str


class CacheEntry(BaseModel):
    """Cache entry model"""
    drug_name: str
    data: dict
    timestamp: datetime
    ttl_hours: int


class SafetyProfile(BaseModel):
    """Drug safety profile output"""
    drug_name: str
    safety_score: float = Field(..., ge=0, le=100)
    summary: str
    adverse_events_count: int = 0
    top_side_effects: List[str] = []
    high_risk_demographics: List[str] = []
    active_recalls: int = 0
    data_freshness: str
    cached: bool


class RecallInfo(BaseModel):
    """Drug recall information"""
    drug_name: str
    recalls: List[dict] = []
    status: str


class DrugComparisonItem(BaseModel):
    """Single item in drug comparison"""
    drug_name: str
    safety_score: float
    top_concern: str


class DrugComparison(BaseModel):
    """Drug comparison result"""
    comparison: List[DrugComparisonItem]
    recommendation: str
