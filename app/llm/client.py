import httpx

from app.schemas import ChatResponse, Message, Usage


class LLMClient:
    """Thin client for any OpenAI-compatible /chat/completions endpoint."""

    def __init__(self, base_url: str, api_key: str, timeout_s: float):
        self._http = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            # LLMs are slow: long read timeout, short connect timeout
            timeout=httpx.Timeout(timeout_s, connect=5.0),
        )

    async def chat(
        self, model: str, messages: list[Message], temperature: float
    ) -> ChatResponse:
        payload = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "stream": False,
        }
        resp = await self._http.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        usage = data.get("usage")
        return ChatResponse(
            model=data.get("model", model),
            message=Message(
                role=choice["message"]["role"],
                content=choice["message"]["content"] or "",
            ),
            finish_reason=choice.get("finish_reason"),
            usage=Usage(**usage) if usage else None,
        )

    async def aclose(self) -> None:
        await self._http.aclose()