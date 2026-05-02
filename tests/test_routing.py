import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.agents.stubs import run_stub_agent, STUB_AGENTS
from src.classifier.schemas import ClassifierOutput, ExtractedEntities

class TestStubAgents:
    @pytest.mark.asyncio
    async def test_all_stub_agents_return_structured_response(self):
        classification = ClassifierOutput(
            intent="market research",
            agent="market_research",
            entities=ExtractedEntities(tickers=["AAPL"]),
            confidence=0.9,
            resolved_query="Tell me about Apple"
        )
        
        for agent_name in STUB_AGENTS:
            chunks = []
            async for chunk in run_stub_agent(agent_name, "test query", classification, {}):
                chunks.append(chunk)
            
            full_response = "".join(chunks)
            data = json.loads(full_response)
            
            assert data["status"] == "not_implemented"
            assert data["agent"] == agent_name
            assert "classified_intent" in data
            assert "message" in data
    
    @pytest.mark.asyncio
    async def test_stub_never_crashes(self):
        classification = ClassifierOutput(
            intent="unknown",
            agent="general",
            entities=ExtractedEntities(),
            confidence=0.0,
            resolved_query=""
        )
        
        # Even with empty/bad inputs, must not raise
        chunks = []
        async for chunk in run_stub_agent("market_research", "", classification, {}):
            chunks.append(chunk)
        
        assert len(chunks) > 0
