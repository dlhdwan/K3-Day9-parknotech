import os

class Config:
    # Model configuration
    MODEL_NAME: str = os.environ.get("MODEL", "gemma2:9b")
    OLLAMA_MODELS_PATH: str = os.environ.get("OLLAMA_MODELS", r"D:\OllamaModels")
    OLLAMA_API_URL: str = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/v1/chat/completions")
    
    # Directory paths
    DATA_DIR: str = "data"
    INPUT_DIR: str = "input"
    OUTPUT_DIR: str = "output"
    LOGGING_DIR: str = "logging"
    TRACE_FILE: str = os.path.join(LOGGING_DIR, "trace.jsonl")
    METADATA_FILE: str = os.path.join(LOGGING_DIR, "metadata.json")

    # API parameters (Optimized for speed & concise responses)
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 120
    REQUEST_TIMEOUT: int = 30
