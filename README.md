# chatlab

A toy chat backend, built step by step to learn AI engineering by recreating the core ideas behind [Open WebUI](https://github.com/open-webui/open-webui).

The premise: a chat app isn't "an AI". It's a stateful backend wrapped around a stateless model API. The LLM does one thing (messages in, next message out); memory, documents, tools, routing, streaming and persistence are the backend's job.

```
Client ──► chatlab backend ──► LLM API (stateless: messages in → message out)
              │
              ├── conversation store
              ├── context builder (history + docs + system prompt)
              ├── tools / agent loop
              └── vector store
```

## Stack

- **Python 3.13 + FastAPI + httpx**, managed with [uv](https://docs.astral.sh/uv/)
- **No LLM SDKs** (for now): the OpenAI-compatible HTTP API is called by hand to see the actual protocol
- **[Ollama](https://ollama.com)** locally for development; any OpenAI-compatible provider works (vLLM, llama.cpp, LM Studio, OpenRouter, OpenAI)
- **curl** as the UI for most of the course

## Progress

Current state: **Lesson 1 done.**

| # | Lesson | Topics | Status |
|---|---|---|---|
| 0 | Setup & mental model | What a chat backend really is | ✅ |
| 1 | First LLM call | Messages, roles, statelessness, tokens, `finish_reason` | ✅ |
| 2 | Streaming | SSE parsing, re-streaming to the client, cancellation | |
| 3 | Conversations & persistence | SQLite schema, chat history, rebuilding context per request | |
| 4 | Context window management | Token counting, truncation, rolling summaries | |
| 5 | Multi-provider abstraction | Adapter pattern, OpenAI vs Anthropic wire formats, model listing | |
| 6 | Prompts & background LLM tasks | System prompt presets, auto titles, follow-up suggestions | |
| 7 | Tool calling | Agent loop, JSON schema tools, parallel calls, safety limits | |
| 8 | RAG part 1 | Ingestion, parsing, chunking | |
| 9 | RAG part 2 | Embeddings, vector store, retrieval, citations | |
| 10 | RAG part 3 | Hybrid search (BM25 + vectors), reranking, query rewriting | |
| 11 | Web search & MCP | Tools from external servers, MCP client | |
| 12 | Observability | Tracing, token/cost/latency metrics, OpenTelemetry GenAI | |
| 13 | Evals | Testing non-deterministic systems, LLM-as-judge, regression sets | |
| 14 | Minimal UI | Consuming the streaming API from a web page | |

## Project layout

```
app/
  main.py        # FastAPI app, lifespan-managed LLM client, POST /api/chat
  config.py      # Settings via pydantic-settings (env vars / .env)
  schemas.py     # Our own API contract (deliberately not the provider's)
  llm/
    client.py    # Thin async client for OpenAI-compatible /chat/completions
```

## Getting started

### 1. Run a model locally

```bash
brew install ollama
ollama serve               # listens on :11434
ollama pull llama3.2
```

### 2. Install and run

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Swagger UI: http://localhost:8000/docs

### 3. Chat

```bash
curl -s localhost:8000/api/chat -H "Content-Type: application/json" -d '{
  "messages": [
    {"role": "system", "content": "You are a terse senior engineer."},
    {"role": "user", "content": "Explain backpressure in one sentence."}
  ]
}' | jq
```

Response shape:

```json
{
  "model": "llama3.2",
  "message": { "role": "assistant", "content": "..." },
  "finish_reason": "stop",
  "usage": { "prompt_tokens": 30, "completion_tokens": 25, "total_tokens": 55 }
}
```

## Configuration

Settings are read from environment variables or a `.env` file:

| Variable | Default | Description |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible base URL |
| `LLM_API_KEY` | `ollama` | API key (Ollama ignores it) |
| `DEFAULT_MODEL` | `llama3.2` | Model used when the request doesn't set one |
| `LLM_TIMEOUT_S` | `120.0` | Read timeout for LLM calls, in seconds |

## API

### `POST /api/chat`

| Field | Type | Notes |
|---|---|---|
| `messages` | `[{role, content}]` | Required, at least one. Roles: `system`, `user`, `assistant` |
| `model` | `string` | Optional, falls back to `DEFAULT_MODEL` |
| `temperature` | `float` | `0.0`–`2.0`, default `0.7` |

Errors: `502` if the provider returns an error, `504` if it times out.

## Notes from Lesson 1

- **The API is stateless.** The model remembers nothing between calls; "chat memory" means resending the whole history every time.
- **Tokens** (input + output) are what you pay for and are limited by. `usage` reports the counts.
- **`finish_reason`**: `stop` means the model finished naturally, `length` means it was cut off by the token limit.
- **Own your contract.** The API schema is separate from the provider's wire format, so swapping providers later doesn't leak into clients.
