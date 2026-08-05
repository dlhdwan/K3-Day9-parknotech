import os
import json
import time
from typing import Any
from src.config import Config

class TraceLogger:
    def __init__(self, log_path: str = None):
        self.log_path = log_path or Config.TRACE_FILE
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
