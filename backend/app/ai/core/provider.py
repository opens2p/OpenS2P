"""
AI provider abstraction — supports local heuristics, OpenAI, and custom models.
"""
from __future__ import annotations
import json
from typing import Any
from app.core.config import settings


class AIProvider:
    """Abstracts AI model calls. Currently uses heuristics;
    swap to OpenAI/anthropic/etc. by setting AI_PROVIDER=openai in env."""

    def __init__(self, model: str | None = None):
        self.model = model or settings.OPENAI_MODEL
        self.provider = settings.AI_PROVIDER
        self.api_key = settings.OPENAI_API_KEY

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Generate AI response. Currently returns heuristic response.
        In production, calls OpenAI/anthropic API."""
        if self.provider == "openai" and self.api_key:
            return await self._call_openai(system_prompt, user_prompt, temperature, max_tokens)
        return self._heuristic_response(system_prompt, user_prompt)

    async def _call_openai(self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> dict[str, Any]:
        import openai
        client = openai.AsyncClient(api_key=self.api_key)
        try:
            resp = await client.chat.completions.create(
                model=self.model, temperature=temperature, max_tokens=max_tokens,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            )
            content = resp.choices[0].message.content or ""
            return {"content": content, "model": self.model, "tokens": resp.usage.total_tokens if resp.usage else 0}
        except Exception as e:
            return {"content": f"AI error: {e}", "model": self.model, "error": str(e)}

    def _heuristic_response(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return structured heuristic response based on prompt keywords."""
        content = self._generate_heuristic(user_prompt)
        return {"content": json.dumps(content), "model": "heuristic", "tokens": 0}

    def _generate_heuristic(self, prompt: str) -> dict[str, Any]:
        prompt_lower = prompt.lower()
        if "risk" in prompt_lower and "supplier" in prompt_lower:
            return {"risk_level": "MEDIUM", "score": 45, "factors": ["Rule-based assessment"], "recommendation": "Review supplier documentation"}
        if "clause" in prompt_lower or "contract" in prompt_lower:
            return {"clauses": [{"type": "TERMINATION", "text": "90 days notice", "risk": "LOW"}], "summary": "Standard contract terms"}
        if "spend" in prompt_lower or "saving" in prompt_lower:
            return {"opportunities": [{"category": "IT Hardware", "potential_saving": 120000, "recommendation": "Consolidate suppliers"}], "total_potential_saving": 120000}
        return {"response": "Analysis complete", "confidence": "HIGH"}
