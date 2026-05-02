# Valura AI Microservice

🎥 Defence Video: [LINK_TO_BE_ADDED]

## Quick Start

```bash
git clone <repo>
cd <repo>
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your OPENAI_API_KEY
uvicorn src.main:app --reload --port 8000
```

## Environment Variables

| Variable | Description |
| --- | --- |
| OPENAI_API_KEY | Your OpenAI API key for intent classification and narrative generation |
| MODEL_DEV | Development model (e.g. gpt-4o-mini) |
| MODEL_EVAL | Evaluation model (e.g. gpt-4.1) |
| ACTIVE_MODEL | Model to use during runtime |
| SESSION_TTL_SECONDS | Time to live for session context in memory |
| REQUEST_TIMEOUT_SECONDS | Timeout for API requests |

## Architecture

The system is designed as a pipeline that processes incoming user queries via SSE stream:
1. **Safety Guard**: Runs first using pure regex to intercept harmful patterns (e.g., market manipulation, money laundering) in <10ms. Allows educational queries to pass.
2. **Intent Classification**: Uses a single LLM call to classify the intent and extract entities, utilizing conversation history to handle context.
3. **Routing**: Directs the request to the appropriate agent based on the classification.
4. **Agent Execution (Portfolio Health)**: Fetches required market data using yfinance, calculates metrics (concentration, performance vs. benchmark), and streams an LLM-generated narrative response.
5. **SSE Streaming**: Sends events back to the client continuously.

## Key Decisions

*   **In-Memory Session Storage**: Used for simplicity, zero-dependency, and <1ms latency during demonstrations. Includes TTL eviction to prevent unbounded growth. In a production scenario, this can be seamlessly swapped to Redis.
*   **One LLM Call for Classification**: Selected to minimize cost and latency while leveraging structured JSON outputs for reliable entity extraction and agent routing.
*   **sse-starlette**: Provides native FastAPI integration and robust handling of backpressure for Server-Sent Events.
*   **yfinance**: Employed for market data as it's free and requires no API key, making it ideal for demos and testing.
*   **Safety Guard Design**: A regex-first approach ensures instantaneous blocking of harmful queries while maintaining an educational override pattern for legitimate research.

## Testing

Tests heavily mock LLM calls, so no OPENAI_API_KEY is needed to run the suite.

```bash
pytest tests/ -v               # run all tests
pytest tests/test_safety.py -v # run only safety tests
```

## Latency Measurement

We measured p95 latency using detailed logging around each pipeline component. The Safety Guard consistently executes in <10ms. The initial Time To First Byte (TTFB) is largely dictated by the Intent Classifier's LLM call, which averages ~500ms-1s depending on the model.

## Cost Estimate

*   **Classifier Call**: ~400 tokens in, ~400 tokens out
*   **Health Agent Call**: ~600 tokens in, ~500 tokens out

Using typical pricing models (e.g., gpt-4o-mini or similar lightweight models), this amounts to well under $0.05 per query, meeting the cost efficiency target.

## What I'd do with more time

*   **Embedding Pre-classifier**: Introduce a fast embedding-based router before the LLM classifier to handle highly common queries at virtually zero cost.
*   **Redis Sessions**: Implement distributed session storage for horizontal scalability.
*   **Per-Tenant Model Routing**: Support routing to different models based on user subscription tiers or specific regional compliance requirements.
