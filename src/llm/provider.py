src/llm/provider.py
import httpx
from ..utils.settings import settings

class Embeddings:
    dim = 1536

    async def embed(self, texts: list[str]) -> list[list[float]]:
        provider = settings.llm_provider.lower()
        if provider == "openai":
            return await self._openai_embed(texts)
        elif provider == "anthropic":
            # Fall back to OpenAI for embeddings if Anthropic selected
            return await self._openai_embed(texts)
        raise RuntimeError("Unknown LLM provider")

    async def _openai_embed(self, texts: list[str]) -> list[list[float]]:
        url = "https://api.openai.com/v1/embeddings"
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, headers=headers, json={"model": settings.embed_model, "input": texts})
            r.raise_for_status()
            data = r.json()["data"]
            return [d["embedding"] for d in data]

class LLM:
    async def summarize_cluster(self, docs: list[str]) -> str:
        prompt = "Summarize the following notes into a concise memory episode:\n\n" + "\n- ".join(docs)
        return await self._chat(prompt)

    async def detect_contradictions(self, facts: list[str]) -> dict:
        prompt = (
            "Given these facts, identify contradictions and propose resolutions with confidence:"
            "\n" + "\n".join(f"- {f}" for f in facts) +
            "\nReturn JSON with fields contradictions:[{a,b,reason}], updates:[{subject,predicate,object,confidence}]"
        )
        txt = await self._chat(prompt)
        try:
            import json
            return json.loads(txt)
        except Exception:
            return {"contradictions": [], "updates": []}

    async def _chat(self, prompt: str) -> str:
        provider = settings.llm_provider.lower()
        if provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "system", "content": "You are a careful reasoning assistant."},
                             {"role": "user", "content": prompt}],
                "temperature": 0
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
        elif provider == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            headers = {"x-api-key": settings.anthropic_api_key, "anthropic-version": "2023-06-01"}
            payload = {"model": "claude-3-5-sonnet-20240620", "max_tokens": 800, "messages":[{"role":"user","content": prompt}]}
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                return r.json()["content"][0]["text"]
        else:
            raise RuntimeError("Unknown LLM provider")