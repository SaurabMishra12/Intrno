import requests


class GeminiAdapter:
    def generate(self, model: str, api_key: str, prompt: str, temperature: float = 0.2) -> str:
        if not api_key:
            raise ValueError("Gemini API key required")
        model_name = model or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        response = requests.post(url, params={"key": api_key}, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
