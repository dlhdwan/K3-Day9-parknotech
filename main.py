import os
import json
import glob
import time
from src.data_loader import OlistDataLoader
from src.agents.coordinator_agent import CoordinatorAgent

# Khai báo model sử dụng theo yêu cầu đề bài (không để trong .env, đặt trực tiếp trong code để chấm)
MODEL_NAME = "qwen3:8b"
MODEL_PARAMS = "8.0B"

FRAMEWORK = "Custom Python Multi-Agent Workflow Engine"
RUNTIME = "Python 3 Standard Library / In-Memory State Graph"

def main():
    print(f"=== Starting K3-Day9 Multi-Agent E-commerce Dispute Resolution ===")
    print(f"Model configured: {MODEL_NAME} ({MODEL_PARAMS})")
    print("1. Initializing Infrastructure Layer & loading Olist dataset CSVs...")
    start_ts = time.perf_counter()
    OlistDataLoader.get_instance(data_dir="data")
    load_time = (time.perf_counter() - start_ts) * 1000
    print(f"   Done loading Olist indexes in {load_time:.2f} ms.")

    print("2. Initializing Coordinator Agent...")
    coordinator = CoordinatorAgent(output_dir="output")

    input_files = sorted(glob.glob(os.path.join("input", "EC_*.json")))
    if not input_files:
        print("WARNING: No EC_*.json input files found in input/ directory.")
        return

    print(f"3. Processing {len(input_files)} customer dispute cases...")
    os.makedirs("logging", exist_ok=True)
    trace_file_path = os.path.join("logging", "trace.jsonl")

    total_events = 0
    with open(trace_file_path, mode="w", encoding="utf-8") as trace_f:
        for file_path in input_files:
            with open(file_path, mode="r", encoding="utf-8") as f:
                raw_input = json.load(f)
            
            case_id = raw_input.get("case_id", os.path.basename(file_path).replace(".json", ""))
            context = coordinator.process_case(raw_input)

            # Write event traces for this case
            for event in context.trace_events:
                trace_f.write(json.dumps(event, ensure_ascii=False) + "\n")
                total_events += 1

    print(f"   Successfully processed {len(input_files)} cases and output JSONs to output/.")
    print(f"   Recorded {total_events} handoff event traces to {trace_file_path}.")

    # Update metadata.json
    metadata = {
        "model": MODEL_NAME,
        "parameters": MODEL_PARAMS,
        "framework": FRAMEWORK,
        "runtime": RUNTIME,
        "architecture_style": "LangGraph/AutoGen inspired deterministic multi-agent state graph with Handoff Contract and Evidence Builder"
    }
    with open(os.path.join("logging", "metadata.json"), mode="w", encoding="utf-8") as mf:
        json.dump(metadata, mf, indent=2, ensure_ascii=False)
    
    print("4. Updated logging/metadata.json successfully.")
    print("=== Multi-Agent execution finished successfully! ===")

if __name__ == "__main__":
    main()
