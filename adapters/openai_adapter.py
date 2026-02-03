import requests


class OpenAIAdapter:
    def generate(self, model: str, api_key: str, prompt: str, temperature: float = 0.2) -> str:
        if not api_key:
            raise ValueError("OpenAI API key required")
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "model": model or "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
