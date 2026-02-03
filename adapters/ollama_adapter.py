import requests


class OllamaAdapter:
    def generate(self, model: str, api_key: str, prompt: str, temperature: float = 0.2) -> str:
        model_name = model or "llama3"
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
