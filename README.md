# Valura AI Microservice

🎥 **Defence Video**: [https://drive.google.com/file/d/1ZZC9aRv9xH5ORNLDqZl0SzFhptgk2hWR/view?usp=sharing]

The intelligence layer behind the Valura wealth management platform. This microservice acts as an AI co-investor, classifying user intents, enforcing financial safety protocols, routing to specialized agents, and streaming responses back via Server-Sent Events (SSE).

## 🚀 Setup & Execution

### Installation

```bash
git clone <repo>
cd <repo>
python -m venv venv
# On Windows: venv\Scripts\activate
# On Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### Running the Server

*Note: You can run the server in a mock demonstration mode without a real API key. By leaving `OPENAI_API_KEY=mock-key` in your `.env` file, the pipeline will instantly return high-quality mocked LLM responses token-by-token.*

```bash
# Start the FastAPI server
uvicorn src.main:app --reload --port 8000
```
Open `http://localhost:8000/` in your browser to view the Swagger API documentation.

### Testing

Tests use `unittest.mock.patch` to mock all LLM network calls, so CI can run without an OpenAI API key.

```bash
# Run the full test suite
pytest tests/ -v
```

## ⚙️ Environment Variables

| Variable | Description |
| --- | --- |
| `OPENAI_API_KEY` | Your OpenAI API key for intent classification and narrative generation. Defaults to `mock-key` for local demo mode. |
| `MODEL_DEV` | Development model (default: `gpt-4o-mini`) |
| `MODEL_EVAL` | Evaluation model (default: `gpt-4.1`) |
| `ACTIVE_MODEL` | Model to use during runtime (default: `gpt-4o-mini`) |
| `SESSION_TTL_SECONDS` | Time to live for session context in memory (default: 3600) |
| `REQUEST_TIMEOUT_SECONDS` | Timeout for API requests (default: 25) |

## 🏗️ Architectural Decisions & Tradeoffs

### 1. In-Memory Session Storage
**Decision:** Session conversation history is stored in an in-memory dictionary (`src/memory/session.py`) instead of Postgres or Redis. 
**Tradeoff Defense:** For this demonstration slice, in-memory storage achieves `<1ms` read/write latency and avoids complex external dependencies (like requiring a Dockerized database instance for reviewers). To prevent unbounded memory growth, I implemented an automatic TTL (Time-To-Live) eviction policy and a rolling 20-turn context window. In a production environment, this `SessionStore` can be seamlessly swapped out for a Redis-backed implementation to support horizontal pod scaling.

### 2. SSE Streaming Implementation
**Decision:** Selected `sse-starlette` as the streaming library.
**Tradeoff Defense:** While it is possible to implement SSE natively using FastAPI's `StreamingResponse` and raw byte generators, `sse-starlette` provides robust, standard-compliant handling of client disconnects and backpressure out of the box. This prevents hanging connections and zombie processes when users navigate away mid-stream. 

### 3. Safety Guard Tradeoff
**Decision:** Built a synchronous, pure-regex local computation engine (`<1ms`) that runs before the LLM. 
**Tradeoff Defense:** We prioritize a zero-latency "hard wall" against non-negotiable financial crimes (insider trading, money laundering) over semantic nuance. I implemented an `EDUCATIONAL_PATTERNS` override that successfully passes queries like *"how does insider trading work?"* However, the tradeoff is that highly complex, edge-case adversarial queries (e.g., a heavily veiled hypothetical scenario) might occasionally trigger a false positive block. In wealth management, the regulatory risk of assisting a financial crime far outweighs the UX cost of over-blocking an edge-case hypothetical. 

### 4. Pipeline Timeout
**Decision:** Hardcoded an `asyncio.wait_for` timeout of 10 seconds for the LLM intent classification, and set a global timeout context of 25 seconds. 
**Tradeoff Defense:** In a chat interface, user abandonment spikes exponentially after 4-5 seconds. If the classifier fails to return within 10 seconds, the system aborts the LLM call and gracefully degrades to the `general_query` stub agent rather than hanging indefinitely.

### 5. Library Choices
*   **FastAPI & Pydantic:** Best-in-class for building robust APIs with strict type validation, ensuring our `ClassifierOutput` schemas perfectly match the fixture taxonomy.
*   **yfinance:** Used within the `portfolio_health` agent to fetch live market data. Chosen because it requires no API keys or authentication, making the demo frictionless while effectively proving the agent architecture.
*   **OpenAI SDK:** Asynchronous client utilization (`AsyncOpenAI`) prevents blocking the main thread during token generation.

## 🔮 What I'd do with more time

*   **Redis Migration:** Replace the in-memory session cache with ElastiCache/Redis for horizontal scaling.
*   **Vector Caching / Pre-Classification:** Add an ultra-low-latency embedding vector search before the LLM intent classifier to immediately route high-frequency/trivial queries (e.g., "hi", "how is my portfolio") without hitting OpenAI.
*   **Agent Parallelization:** For heavy agents (like `risk_assessment`), spawn background workers (Celery/Kafka) and use SSE to stream progress updates (`"Calculating VaR..."`) to keep the user engaged while waiting for the final output.
