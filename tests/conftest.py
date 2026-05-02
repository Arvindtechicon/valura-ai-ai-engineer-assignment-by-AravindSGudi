import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

# Mock classifier response factory
def make_mock_classifier_response(agent: str, intent: str, tickers: list = None, entities_extra: dict = None):
    entities = {"tickers": tickers or [], "sectors": [], "topics": [], "amount": None, "currency": None, "period_years": None, "rate": None}
    if entities_extra:
        entities.update(entities_extra)
    
    return json.dumps({
        "intent": intent,
        "agent": agent,
        "entities": entities,
        "safety_note": None,
        "confidence": 0.95,
        "resolved_query": intent
    })

@pytest.fixture
def mock_openai_classifier(monkeypatch):
    """Mock OpenAI for classifier tests."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = make_mock_classifier_response(
        agent="portfolio_health",
        intent="portfolio health check",
        tickers=[]
    )
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    with patch("src.classifier.intent.AsyncOpenAI", return_value=mock_client):
        yield mock_client

@pytest.fixture
def mock_openai_streaming(monkeypatch):
    """Mock OpenAI streaming for portfolio health narrative."""
    async def fake_stream():
        chunks = ["Your portfolio ", "looks healthy. ", "Consider diversifying."]
        for c in chunks:
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta.content = c
            yield mock_chunk
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=fake_stream())
    
    with patch("src.agents.portfolio_health.AsyncOpenAI", return_value=mock_client):
        yield mock_client

@pytest.fixture
def sample_user_context():
    return {
        "user_id": "user_001",
        "risk_profile": "aggressive",
        "currency": "USD",
        "country": "US",
        "holdings": [
            {"ticker": "NVDA", "quantity": 100, "avg_cost": 400.0, "current_value": 80000.0},
            {"ticker": "AAPL", "quantity": 50, "avg_cost": 150.0, "current_value": 9000.0},
            {"ticker": "MSFT", "quantity": 20, "avg_cost": 300.0, "current_value": 8000.0},
        ],
        "kyc_status": "verified"
    }

@pytest.fixture
def empty_user_context():
    return {
        "user_id": "user_004",
        "risk_profile": "moderate",
        "currency": "USD",
        "country": "US",
        "holdings": [],
        "kyc_status": "verified"
    }
