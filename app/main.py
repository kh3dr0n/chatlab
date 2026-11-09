from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request

from app.config import settings
from app.llm.client import LLMClient
from app.schemas import ChatRequest, ChatResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One shared client = one connection pool (like a singleton bean)
    app.state.llm = LLMClient(
        settings.llm_base_url, settings.llm_api_key, settings.llm_timeout_s
    )
    yield
    await app.state.llm.aclose()


app = FastAPI(title="chatlab", lifespan=lifespan)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    llm: LLMClient = request.app.state.llm
    try:
        return await llm.chat(
            model=req.model or settings.default_model,
            messages=req.messages,
            temperature=req.temperature,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e.response.text}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LLM timed out")