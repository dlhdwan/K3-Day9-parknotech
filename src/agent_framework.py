import os
import json
import urllib.request
import urllib.error
import time
from typing import Dict, Any, List, Optional

def load_env(env_path: str = ".env"):
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip().upper()] = v.strip().strip("'\"")

class GroqLLMClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        load_env()
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = model or os.environ.get("MODEL", "llama-3.1-8b-instant")
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def chat_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 500) -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment or .env file.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        data_bytes = json.dumps(payload).encode("utf-8")

        for attempt in range(8):
            req = urllib.request.Request(self.url, data=data_bytes, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    res_body = json.loads(response.read().decode("utf-8"))
                    return res_body["choices"][0]["message"]["content"].strip()
            except urllib.error.HTTPError as http_err:
                if http_err.code == 429:
                    retry_after = http_err.headers.get("Retry-After")
                    sleep_time = float(retry_after) if retry_after else (4.0 * (attempt + 1))
                    print(f"[Rate Limit 429] Groq rate limited. Sleeping for {sleep_time:.1f}s (Attempt {attempt+1}/8)...")
                    time.sleep(sleep_time)
                else:
                    if attempt == 7:
                        print(f"Groq API HTTP Error {http_err.code}: {http_err}")
                        raise http_err
                    time.sleep(2.0)
            except Exception as e:
                if attempt == 7:
                    print(f"Groq API Error after 8 attempts: {e}")
                    raise e
                time.sleep(2.0)

        return ""

class TraceLogger:
    def __init__(self, log_path: str = "logging/trace.jsonl"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_step(self, case_id: str, agent_name: str, action: str, input_payload: Any, output_payload: Any):
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "case_id": case_id,
            "agent": agent_name,
            "action": action,
            "input": input_payload,
            "output": output_payload
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

class BaseAgent:
    def __init__(self, name: str, role: str, system_prompt: str, llm_client: GroqLLMClient, trace_logger: TraceLogger):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm_client = llm_client
        self.trace_logger = trace_logger

    def run(self, case_id: str, prompt: str, context: Dict[str, Any]) -> str:
        # Pacing to avoid hitting Groq RPM limit
        time.sleep(0.5)

        full_user_prompt = f"Context:\n{json.dumps(context, indent=2, ensure_ascii=False)}\n\nPrompt:\n{prompt}"
        response = self.llm_client.chat_completion(
            system_prompt=self.system_prompt,
            user_prompt=full_user_prompt
        )
        self.trace_logger.log_step(
            case_id=case_id,
            agent_name=self.name,
            action=self.role,
            input_payload={"prompt": prompt, "context_keys": list(context.keys())},
            output_payload=response
        )
        return response
