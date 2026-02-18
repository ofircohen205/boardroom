from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


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
