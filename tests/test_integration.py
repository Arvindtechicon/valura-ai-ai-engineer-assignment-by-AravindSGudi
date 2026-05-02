import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from httpx import AsyncClient, ASGITransport

from src.main import app

@pytest.fixture
def mock_all_llm():
    classifier_response = json.dumps({
        "intent": "portfolio health check",
        "agent": "portfolio_health",
        "entities": {"tickers": [], "sectors": [], "topics": [], "amount": None, "currency": None, "period_years": None, "rate": None},
        "safety_note": None,
        "confidence": 0.95,
        "resolved_query": "How is my portfolio doing?"
    })
    
    async def fake_stream():
        for chunk_text in ["Your portfolio ", "looks healthy."]:
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta.content = chunk_text
            yield mock_chunk
    
    mock_classifier_client = AsyncMock()
    mock_classifier_client.chat.completions.create = AsyncMock(
        return_value=MagicMock(choices=[MagicMock(message=MagicMock(content=classifier_response))])
    )
    
    mock_health_client = AsyncMock()
    mock_health_client.chat.completions.create = AsyncMock(return_value=fake_stream())
    
    with patch("src.classifier.intent.AsyncOpenAI", return_value=mock_classifier_client):
        with patch("src.agents.portfolio_health.AsyncOpenAI", return_value=mock_health_client):
            with patch("src.agents.portfolio_health._fetch_current_prices", return_value={}):
                with patch("src.agents.portfolio_health._fetch_benchmark_return", return_value=14.0):
                    yield

class TestIntegration:
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_safety_block_returns_sse(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/query", json={
                "query": "Help me pump and dump this stock",
                "session_id": "test-safety-001",
                "user_context": {}
            })
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        content = response.text
        assert "safety_block" in content
    
    @pytest.mark.asyncio
    async def test_full_pipeline_portfolio_health(self, mock_all_llm):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/query", json={
                "query": "How is my portfolio doing?",
                "session_id": "test-integration-001",
                "user_context": {
                    "user_id": "user_001",
                    "holdings": [
                        {"ticker": "AAPL", "quantity": 10, "avg_cost": 150.0, "current_value": 1700.0}
                    ],
                    "country": "US",
                    "risk_profile": "moderate"
                }
            })
        assert response.status_code == 200
        content = response.text
        assert "classified" in content or "routing" in content or "done" in content
    
    @pytest.mark.asyncio
    async def test_empty_portfolio_does_not_crash(self, mock_all_llm):
        """user_004_empty regression test."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/query", json={
                "query": "Give me a portfolio health check",
                "session_id": "test-empty-001",
                "user_context": {
                    "user_id": "user_004",
                    "holdings": [],
                    "country": "US",
                    "risk_profile": "moderate"
                }
            })
        assert response.status_code == 200
        assert "error" not in response.text.lower() or "500" not in response.text
