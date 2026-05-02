import json
import logging
from openai import AsyncOpenAI
from src.config import settings
from src.classifier.schemas import ClassifierOutput, ExtractedEntities
from src.memory.session import session_store

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an intent classifier for Valura, a wealth management platform. 

Given a user query and conversation history, return a single JSON object with these fields:
- intent: brief description of what the user wants (string)
- agent: one of exactly: portfolio_health, market_research, investment_strategy, financial_planning, financial_calculator, risk_assessment, product_recommendation, predictive_analysis, customer_support, general_query
- entities: object with optional fields: tickers (array of uppercase strings), sectors (array), topics (array), amount (number), currency (string), period_years (number), rate (number), frequency (string), horizon (string), time_period (string), index (string), action (string), goal (string)
- safety_note: null or a brief note if the query touches sensitive but not blocked territory (informational only)
- confidence: float 0-1
- resolved_query: the user's query with any pronoun/reference resolved using conversation history

Agent selection rules:
- portfolio_health: any question about the user's own portfolio status, health, diversification, performance
- market_research: questions about specific stocks, sectors, market news, company fundamentals
- investment_strategy: how to invest, allocation strategy, asset class selection, rebalancing strategy
- financial_planning: long-term planning, retirement, goals, savings rate
- financial_calculator: compound interest, returns calculation, SIP, mortgage, tax calculations, FX conversion
- risk_assessment: risk profile questions, volatility, drawdown, VaR, beta analysis, what-if scenarios
- product_recommendation: recommend specific products/funds matching user profile
- predictive_analysis: price predictions, forecasts, future performance
- customer_support: account issues, platform help, non-financial questions
- general_query: anything else, educational, conversational, definitions

Return ONLY valid JSON. No markdown. No explanation."""

FALLBACK_OUTPUT = ClassifierOutput(
    intent="unknown",
    agent="general_query",
    entities=ExtractedEntities(),
    confidence=0.0,
    resolved_query="",
    safety_note="Classifier unavailable — routed to general handler"
)

async def classify_intent(
    query: str,
    session_id: str,
    user_context: dict | None = None
) -> ClassifierOutput:
    history = session_store.get_history(session_id)
    
    # Build context string from history (last 4 turns for context window efficiency)
    history_str = ""
    if history:
        recent = history[-4:]
        history_str = "\n".join(f"{t['role'].upper()}: {t['content']}" for t in recent)
        history_str = f"\n\nConversation history:\n{history_str}"
    
    user_message = f"Query: {query}{history_str}"
    
    if settings.openai_api_key == "mock-key":
        import asyncio
        await asyncio.sleep(0.5)
        return ClassifierOutput(
            intent="portfolio health check",
            agent="portfolio_health",
            entities=ExtractedEntities(),
            confidence=0.99,
            resolved_query=query
        )
    
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    try:
        response = await client.chat.completions.create(
            model=settings.active_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=400,
            timeout=10.0
        )
        
        raw = response.choices[0].message.content
        data = json.loads(raw)
        
        # Normalise tickers to uppercase
        if "entities" in data and "tickers" in data["entities"]:
            data["entities"]["tickers"] = [t.upper() for t in data["entities"]["tickers"]]
        
        result = ClassifierOutput(**data)
        if not result.resolved_query:
            result.resolved_query = query
        return result
        
    except Exception as e:
        logger.error(f"Classifier error for session {session_id}: {e}")
        fallback = FALLBACK_OUTPUT.model_copy()
        fallback.resolved_query = query
        return fallback
