from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class DecisionSchema(BaseModel):
    action: str
    confidence: float
    rationale: str


class AnalysisHistoryItemSchema(BaseModel):
    id: UUID
    ticker: str
    market: str
    created_at: datetime
    decision: Optional[DecisionSchema] = None
