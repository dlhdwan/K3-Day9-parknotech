import os
import json
import glob
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config import Config
from src.llm_client import OllamaLLMClient
from src.trace_logger import TraceLogger
from src.data_loader import OlistDataLoader
from src.agents import (
    CoordinatorAgent,
    OrderSellerInvestigator,
    FinancialReconciler,
    LogisticsDeliveryInvestigator,
    AdversarialAuditor,
    PolicyAdjudicator,
    ComplianceGuard
)

def write_metadata():
    metadata = {
        "model": Config.MODEL_NAME,
        "parameter_size": "9B",
        "framework": "Concurrent Multi-Agent Architecture (Parallel Execution Protocol)",
        "runtime": "Local Ollama (D:\\OllamaModels) / Python 3.12",
        "dataset": "Olist Brazilian E-Commerce Dataset",
        "agents": [
            "CoordinatorAgent",
            "OrderSellerInvestigator",
            "FinancialReconciler",
            "LogisticsDeliveryInvestigator",
            "AdversarialAuditor",
            "PolicyAdjudicator",
            "ComplianceGuard"
        ],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    os.makedirs(Config.LOGGING_DIR, exist_ok=True)
    with open(Config.METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"Wrote {Config.METADATA_FILE}", flush=True)

def process_single_case(case_file: str, data_loader: OlistDataLoader, llm_client: OllamaLLMClient, trace_logger: TraceLogger):
    with open(case_file, "r", encoding="utf-8") as f:
        case_data = json.load(f)

    case_id = case_data["case_id"]
    
    # Initialize per-worker agent instances for thread safety
    coordinator = CoordinatorAgent(llm_client, trace_logger)
    order_investigator = OrderSellerInvestigator(llm_client, trace_logger)
    fin_reconciler = FinancialReconciler(llm_client, trace_logger)
    delivery_investigator = LogisticsDeliveryInvestigator(llm_client, trace_logger)
    auditor = AdversarialAuditor(llm_client, trace_logger)
    adjudicator = PolicyAdjudicator(llm_client, trace_logger)
    compliance_guard = ComplianceGuard(llm_client, trace_logger)

    # Step 1: Coordinator Intake
    intake_res = coordinator.process(case_data)
    claimed_order_id = intake_res["claimed_order_id"]

    # Step 2: Query relational database
    order_data = data_loader.get_order_analysis(claimed_order_id)
    if not order_data.get("exists"):
        return case_id, False, f"Order {claimed_order_id} not found"

    # Step 3: Domain Investigations
    order_inv_res = order_investigator.process(case_id, order_data)
    fin_inv_res = fin_reconciler.process(case_id, order_data)
    del_inv_res = delivery_investigator.process(case_id, order_data)

    # Step 4: Adversarial Audit
    audit_res = auditor.process(case_id, intake_res, order_inv_res, fin_inv_res, del_inv_res, order_data)

    # Step 5: Policy Adjudication
    adjudication_res = adjudicator.process(case_id, order_data, audit_res)

    # Step 6: Compliance & Output Guard
    final_output = compliance_guard.process(case_id, claimed_order_id, order_data, adjudication_res)

    # Write output file
    out_filepath = os.path.join(Config.OUTPUT_DIR, f"{case_id}.json")
    with open(out_filepath, "w", encoding="utf-8") as out_f:
        json.dump(final_output, out_f, indent=2, ensure_ascii=False)

    return case_id, True, final_output

def main():
    print(f"=== Starting Accelerated Concurrent Multi-Agent Pipeline ({Config.MODEL_NAME}) ===", flush=True)
    start_time = time.time()
    
    data_loader = OlistDataLoader(data_dir=Config.DATA_DIR)
    llm_client = OllamaLLMClient(model=Config.MODEL_NAME)
    
    os.makedirs(Config.LOGGING_DIR, exist_ok=True)
    if os.path.exists(Config.TRACE_FILE):
        os.remove(Config.TRACE_FILE)
    trace_logger = TraceLogger(Config.TRACE_FILE)

    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

    input_files = sorted(glob.glob(os.path.join(Config.INPUT_DIR, "EC_*.json")))
    print(f"Found {len(input_files)} dispute cases. Executing with 4 parallel worker threads...", flush=True)

    completed = 0
    max_workers = 4

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_case = {
            executor.submit(process_single_case, fpath, data_loader, llm_client, trace_logger): fpath
            for fpath in input_files
        }

        for future in as_completed(future_to_case):
            completed += 1
            case_id, success, res = future.result()
            if success:
                issue = res["assessment"]["primary_issue"]
                refund = res["financial_resolution"]["recommended_refund_brl"]
                print(f"[{completed}/{len(input_files)}] Finished {case_id} | Issue: {issue} | Refund: {refund} BRL", flush=True)
            else:
                print(f"[{completed}/{len(input_files)}] Error on {case_id}: {res}", flush=True)

    elapsed = time.time() - start_time
    write_metadata()
    print(f"\n=== Pipeline Completed in {elapsed:.1f}s ({elapsed/len(input_files):.1f}s/case) ===", flush=True)

if __name__ == "__main__":
    main()
