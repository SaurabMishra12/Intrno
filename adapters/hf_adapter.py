import requests


class HuggingFaceAdapter:
    def generate(self, model: str, api_key: str, prompt: str, temperature: float = 0.2) -> str:
        if not api_key:
            raise ValueError("HuggingFace API key required")
        model_name = model or "mistralai/Mistral-7B-Instruct-v0.2"
        url = f"https://api-inference.huggingface.co/models/{model_name}"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"inputs": prompt, "parameters": {"temperature": temperature}}
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data:
            return data[0].get("generated_text", "").strip()
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"].strip()
        return str(data)
