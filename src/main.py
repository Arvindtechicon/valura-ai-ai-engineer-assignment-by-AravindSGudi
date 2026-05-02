import asyncio
import json
import logging
import uuid
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.config import settings
from src.safety.guard import check_safety
from src.classifier.intent import classify_intent
from src.agents.portfolio_health import run_portfolio_health
from src.agents.stubs import run_stub_agent, STUB_AGENTS
from src.memory.session import session_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Valura AI Microservice",
    description="AI co-investor agent ecosystem for Valura wealth management platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Request/Response schemas ──────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_context: dict = Field(default_factory=dict)
    # user_context shape:
    # {
    #   "user_id": "user_001",
    #   "risk_profile": "aggressive",
    #   "currency": "USD",
    #   "country": "US",
    #   "holdings": [{"ticker": "AAPL", "quantity": 10, "avg_cost": 150.0}],
    #   "kyc_status": "verified"
    # }

# ── Pipeline ──────────────────────────────────────────────────────────────────

async def pipeline(request: QueryRequest) -> AsyncGenerator[str, None]:
    """
    Full pipeline: Safety → Classify → Route → Stream
    Yields SSE-formatted strings.
    """
    query = request.query.strip()
    session_id = request.session_id
    
    try:
        # 1. SAFETY GUARD — runs first, no LLM
        is_blocked, category, safety_message = check_safety(query)
        
        if is_blocked:
            yield f"event: safety_block\ndata: {json.dumps({'blocked': True, 'category': category, 'message': safety_message})}\n\n"
            return
        
        # 2. INTENT CLASSIFICATION — single LLM call
        yield f"event: classifying\ndata: {json.dumps({'status': 'classifying'})}\n\n"
        
        classification = await asyncio.wait_for(
            classify_intent(query, session_id, request.user_context),
            timeout=10.0
        )
        
        yield f"event: classified\ndata: {classification.model_dump_json()}\n\n"
        
        # 3. STORE USER TURN in session memory
        session_store.add_turn(session_id, "user", query)
        
        # 4. ROUTE TO AGENT
        agent_name = classification.agent
        
        yield f"event: routing\ndata: {json.dumps({'agent': agent_name})}\n\n"
        
        # Buffer for session memory (collect full response)
        full_response_parts = []
        
        if agent_name == "portfolio_health":
            async for chunk in run_portfolio_health(
                query=classification.resolved_query or query,
                user_context=request.user_context,
                session_id=session_id
            ):
                full_response_parts.append(chunk)
                # Don't stream the structured data prefix — that's metadata
                if not chunk.startswith("[STRUCTURED_DATA]"):
                    yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"
                else:
                    # Extract and emit structured data as its own event
                    structured_json = chunk[len("[STRUCTURED_DATA]"):]
                    yield f"event: structured_data\ndata: {structured_json}\n\n"
        
        elif agent_name in STUB_AGENTS:
            async for chunk in run_stub_agent(
                agent_name=agent_name,
                query=classification.resolved_query or query,
                classification=classification,
                user_context=request.user_context
            ):
                full_response_parts.append(chunk)
                yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"
        
        else:
            # Unknown agent — safe fallback
            msg = f"No handler registered for agent '{agent_name}'."
            yield f"event: token\ndata: {json.dumps({'text': msg})}\n\n"
            full_response_parts.append(msg)
        
        # 5. STORE ASSISTANT TURN
        full_response = "".join(full_response_parts)
        session_store.add_turn(session_id, "assistant", full_response[:500])  # truncate for memory
        
        # 6. DONE event
        yield f"event: done\ndata: {json.dumps({'session_id': session_id, 'agent_used': agent_name})}\n\n"
    
    except asyncio.TimeoutError:
        yield f"event: error\ndata: {json.dumps({'error': 'timeout', 'message': 'The request timed out. Please try again.'})}\n\n"
    
    except Exception as e:
        logger.error(f"Pipeline error for session {session_id}: {e}", exc_info=True)
        yield f"event: error\ndata: {json.dumps({'error': 'internal_error', 'message': 'An unexpected error occurred. Our team has been notified.'})}\n\n"

# ── Endpoint ──────────────────────────────────────────────────────────────────

from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    """Redirect to the Swagger UI documentation."""
    return RedirectResponse(url="/docs")

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    """
    Single entry point. Accepts user query + context, returns SSE stream.
    Events: classifying | classified | routing | structured_data | token | safety_block | error | done
    """
    return EventSourceResponse(
        pipeline(request),
        media_type="text/event-stream"
    )

@app.get("/health")
async def health_check():
    return {"status": "ok", "model": settings.active_model}

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    session_store.clear(session_id)
    return {"cleared": session_id}
