from typing import AsyncGenerator
from src.classifier.schemas import ClassifierOutput
import json

STUB_AGENTS = {
    "market_research",
    "investment_strategy",
    "financial_planning",
    "financial_calculator",
    "risk_assessment",
    "product_recommendation",
    "predictive_analysis",
    "customer_support",
    "general_query"
}

async def run_stub_agent(
    agent_name: str,
    query: str,
    classification: ClassifierOutput,
    user_context: dict
) -> AsyncGenerator[str, None]:
    """
    Returns a structured not-implemented response for any agent
    that hasn't been built yet. Never crashes.
    """
    response = {
        "status": "not_implemented",
        "agent": agent_name,
        "classified_intent": classification.intent,
        "entities": classification.entities.model_dump(),
        "message": (
            f"The {agent_name.replace('_', ' ').title()} agent is not yet available in this build. "
            f"Your query has been classified correctly and would be handled by this agent in the full system. "
            f"Intent detected: {classification.intent}."
        ),
        "resolved_query": classification.resolved_query
    }
    yield json.dumps(response, indent=2)
