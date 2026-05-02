from pydantic import BaseModel, Field
from typing import Optional, Literal

class ExtractedEntities(BaseModel):
    tickers: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    amount: Optional[float] = None
    currency: Optional[str] = None
    period_years: Optional[float] = None
    rate: Optional[float] = None
    frequency: Optional[str] = None
    horizon: Optional[str] = None
    time_period: Optional[str] = None
    index: Optional[str] = None
    action: Optional[str] = None
    goal: Optional[str] = None
    
class ClassifierOutput(BaseModel):
    intent: str
    agent: Literal[
        "portfolio_health",
        "market_research", 
        "investment_strategy",
        "financial_planning",
        "financial_calculator",
        "risk_assessment",
        "product_recommendation",
        "predictive_analysis",
        "customer_support",
        "general_query"
    ]
    entities: ExtractedEntities
    safety_note: Optional[str] = None  # informational only, does not block
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    resolved_query: str  # follow-up resolved against conversation history
