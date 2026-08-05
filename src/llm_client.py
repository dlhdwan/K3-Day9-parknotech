import json
import urllib.request
import urllib.error
from typing import Optional

class OllamaClient:
    """
    Client for communicating directly with Ollama Local API (http://localhost:11434)
    using model <= 10B parameters (default: qwen2.5:7b-instruct).
    Provides safe fallback if local server is unreachable or timed out.
    """
    _instance = None

    def __init__(self, host: str = "http://localhost:11434", default_model: str = "qwen3:8b", timeout_sec: float = 3.0):
        self.host = host.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout_sec
        self.is_available = self._check_availability_and_resolve_model()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _check_availability_and_resolve_model(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                    print(f"[OllamaClient] Connected successfully to local Ollama server at {self.host}")
                    print(f"[OllamaClient] Available local models: {models}")
                    print(f"[OllamaClient] Active target model configured: {self.default_model}")
                    return True
        except (urllib.error.URLError, TimeoutError, Exception) as e:
            print(f"[OllamaClient] WARNING: Ollama local server at {self.host} not reachable ({e}). Using instantaneous Rule-Based context fallback.")
            return False
        return False

    def generate(self, prompt: str, model: Optional[str] = None) -> str:
        if not self.is_available:
            return "[Ollama Offline] Rule-Based Deterministic Analysis"

        target_model = model or self.default_model
        url = f"{self.host}/api/generate"
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 45
            }
        }
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                response_text = result.get("response", "").strip()
                return response_text
        except Exception as e:
            return f"[LLM Timeout/Error] Rule-Based Fallback ({str(e)[:40]})"

    def analyze_case_intent(self, vi_message: str, claimed_order_id: str) -> str:
        prompt = (
            f"You are an e-commerce dispute investigator. Summarize the customer complaint into one concise English sentence describing the issue.\n"
            f"Vietnamese Complaint: \"{vi_message}\"\n"
            f"Order ID: {claimed_order_id}\n"
            f"English Summary:"
        )
        result = self.generate(prompt)
        if result.startswith("[") and "Fallback" in result or result.startswith("[Ollama"):
            return f"Customer requests delay investigation and rights check for order {claimed_order_id}."
        return result
