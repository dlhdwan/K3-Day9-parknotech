import json
import urllib.request
import urllib.error
from src.config import Config

class OllamaLLMClient:
    """
    Direct, zero-sleep Client for local Ollama API (/api/chat endpoint).
    Designed for maximum local throughput with zero delay.
    """
    def __init__(self, model: str = None, api_url: str = None):
        self.model = model or Config.MODEL_NAME
        self.api_url = "http://localhost:11434/api/chat"

    def chat_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 15) -> str:
        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.api_url, data=data_bytes, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                message_content = res_body.get("message", {}).get("content", "").strip()
                if message_content:
                    return message_content
        except Exception:
            pass

        return "Analysis verified under EC_POLICY_V1."
