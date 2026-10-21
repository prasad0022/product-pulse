"""Optional Gemini structured-output provider."""
import json
import os

class GeminiProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("Install google-genai to use the Gemini provider.") from exc
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not configured for the optional Gemini provider.")
        self.client = genai.Client(api_key=key)
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    def generate_json(self, prompt: str) -> dict:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("LLM returned an empty response.")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("LLM returned invalid JSON.") from exc
