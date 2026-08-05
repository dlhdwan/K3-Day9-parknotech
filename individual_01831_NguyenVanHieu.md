# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                                        |
| --------------- | --------------------------------------------------------------- |
| Họ và tên       | Nguyễn Văn Hiệu                                                 |
| MSSV            | 01831                                                           |
| Khóa/Lớp        | K3 - AI Engineer / Advanced Agentic Architectures               |
| Vai trò chính   | Core Architecture & Verification Lead / Policy & Reasoning Engineer |
| Ngày hoàn thành | 2026-08-05                                                      |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | ------------------ | -------------- | --------------- | ---------- |
| **Hệ thống Kiểm định & Làm tròn Tài chính** | `src/agents/verifier_agent.py`<br>`src/context.py`<br>`src/evidence.py` | `DisputeContext` chứa dữ liệu thô từ CSV và quyết định preliminary từ PolicyAgent | Cấu trúc dữ liệu JSON hoàn chỉnh được chuẩn hóa tài chính (`ROUND_HALF_UP`), bộ bằng chứng Evidence IDs được dedup & sắp xếp theo độ ưu tiên | Hoàn thành |
| **Quy tắc Nghị sự & Xử lý Tranh chấp** | `src/agents/policy_agent.py` | Trạng thái giao hàng, kết quả đối soát thanh toán và cờ vi phạm bàn giao carrier | Cấu trúc `PolicyDecision` chuẩn hóa 100% với danh mục nguyên nhân gốc (`root_cause_code`), mức tiền hoàn và các bên chịu trách nhiệm | Hoàn thành |
| **Điều phối Workflow & Đóng gói Output** | `main.py`<br>`src/agents/coordinator_agent.py`<br>`src/llm_client.py` | 50 file input JSON (`input/EC_*.json`) cùng tin nhắn khiếu nại bằng tiếng Việt | Chuỗi sự kiện log Handoff `logging/trace.jsonl`, 50 file kết quả tại `output/` và file nén nộp bài chuẩn `output.zip` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ----------------------------- | ------- |
| **Tích hợp Tool-using & Phân chia trách nhiệm Logistics** | Hỗ trợ module `DeliveryAgent` (`src/agents/delivery_agent.py`, `src/tools.py`) | Cơ chế truy vấn mốc thời gian qua `DeliveryAuditTool`, giúp phân biệt rõ thời điểm nhận hàng của đơn vị vận chuyển với hạn mức `shipping_limit_date` của nhà bán. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------- | --------------------------- | ---------------- | ------------- |
| Xây dựng và áp dụng cơ chế làm tròn tài chính chính xác `ROUND_HALF_UP` cho toàn bộ luồng định danh và thanh toán | `src/context.py` (`round_currency`)<br>`src/agents/verifier_agent.py` | Trình thâu tóm và loại bỏ mọi sai sót 0.01 BRL do lỗi làm tròn nhị phân trong `financial_resolution` | Chạy `.venv/bin/python scratch/validate_50_cases_schema.py` |
| Tối ưu luồng phán quyết nghiệp vụ, loại bỏ lỗi False Positive về bằng chứng và chuẩn hóa hệ thống nén bài nộp | `src/agents/policy_agent.py`<br>`main.py` | Bàn giao trọn vẹn bộ 50 file JSON hợp lệ tại `output/` và đóng gói file `output.zip` đạt 100% tuân thủ schema đề bài | Chạy `.venv/bin/python main.py` và kiểm tra file nén bằng `ls -l output.zip` |

**Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:**

Báo cáo kiểm định 50 cases (`scratch/validate_50_cases_schema.py`) và hệ thống chấm điểm tự động Benchmark ghi nhận kết quả tổng thể và trọn vẹn của bộ file `output.zip` như sau:
- **Tổng điểm (Total Score): `94.5850` / 100**

**Bảng chi tiết điểm số theo từng hạng mục trọng số:**

| Hạng mục đánh giá | Trọng số | Điểm số đạt được | Đánh giá từ phần việc cá nhân |
| :--- | :---: | :---: | :--- |
| **Tài chính (Financial Resolution)** | 20% | **`95.9877`** | Đạt độ chính xác xuất sắc nhờ tích hợp làm tròn `ROUND_HALF_UP` và kiểm tra sai số ranh giới trong VerifierAgent. |
| **Hành động xử lý (Resolution Actions)** | 10% | **`95.4870`** | Chuẩn hóa ánh xạ hành động (`refund_freight`, `issue_full_refund`, `explain_valid_split_payment`) trong PolicyAgent. |
| **Đánh giá case (Primary Issue & Confidence)** | 20% | **`94.6204`** | Hiệu chỉnh độ tự tin (Confidence calibration: 0.98 - 0.92) và phân thứ tự ưu tiên chuẩn theo bảng nghiệp vụ. |
| **Entity liên quan (Affected Entities)** | 20% | **`94.4659`** | Tổ chức, lọc trùng và tuân thủ giới hạn tối đa 5 ID trên mỗi mảng entity bị ảnh hưởng. |
| **Nguyên nhân gốc (Root Cause & Responsible Parties)** | 15% | **`94.3792`** | Định danh chính xác `OLIST_PLATFORM`, `LOGISTICS_PROVIDER` và mã lỗi vi phạm. |
| **Bằng chứng (Evidence IDs)** | 15% | **`92.4308`** | Áp dụng `EvidenceBuilder` lọc theo thứ tự quan hệ thực thể (order $\rightarrow$ item $\rightarrow$ payment $\rightarrow$ seller $\rightarrow$ policy), triệt tiêu hoàn toàn án phạt Hard Gate vì Bằng chứng giả định (False Positive). |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Trong quá trình xử lý 50 ca khiếu nại thương mại điện tử, hệ thống đối mặt với 3 vấn đề kỹ thuật trọng tâm:
1. **Lỗi lệch sai số làm tròn tài chính:** Sử dụng hàm số thực thuần túy của Python (floating-point arithmetic) dẫn đến chênh lệch 0.01 BRL khi so sánh và hoàn tiền đối soát chi phí vận chuyển hoặc thanh toán chia nhỏ.
2. **Lỗi vi phạm Schema & False Positive bằng chứng (Hard Gate):** Các chuỗi bằng chứng không hợp lệ (như `"policy:EC_POLICY_V1"`) và gán nhầm danh tính nhà cung cấp dịch vụ gây ra điểm số 0 hoặc bị hệ thống chấm điểm tự động từ chối.
3. **Mâu thuẫn thứ tự ưu tiên (Policy Priority Mismatch):** Khi đơn hàng vừa bị giao muộn vừa có nhiều dòng thanh toán (split payments), cần hệ thống xác định đúng ưu tiên hoàn trả tiền giao hàng thay vì trả về thông báo giải thích thanh toán.

### Cách triển khai
- **Hệ thống làm tròn tài chính chủ động:** Thiết lập hàm `round_currency` dùng `decimal.Decimal` áp dụng chiến lược `ROUND_HALF_UP`, tích hợp xuyên suốt ở `OrderAgent`, `PaymentAgent` và trước khi ra phán quyết tại `VerifierAgent`.
- **Pipeline Xử lý Bằng chứng (EvidenceBuilder):** Biến đổi chuỗi bằng chứng thu thập được qua 4 giai đoạn tinh gọn: Chuẩn hóa (Normalize) $\rightarrow$ Khử trùng lặp (Deduplication) $\rightarrow$ Sắp xếp ưu tiên theo quan hệ thực thể (`order` $\rightarrow$ `item` $\rightarrow$ `payment` $\rightarrow$ `seller` $\rightarrow$ `policy`) $\rightarrow$ Cắt ngưỡng tối đa 10 phần tử theo quy chế đề thi.
- **Tối ưu cây phán quyết trong PolicyAgent:** Triển khai chuỗi ưu tiên logic chặt chẽ: Kiểm tra Đơn Hủy (`canceled`) / Đơn Không sẵn sàng (`unavailable`) trước tiên $\rightarrow$ Tiếp đến kiểm tra giao muộn do nhà bán hoặc đơn vị vận chuyển $\rightarrow$ Mới thi hành đối soát Split Payment. Cố định danh tính `party_id` cho platform là `OLIST_PLATFORM` và cho logistics là `LOGISTICS_PROVIDER`.
- **Đóng gói quy trình độc lập:** Thêm logic sử dụng `zipfile` ngay tại đoạn kết của `main.py` để đóng gói 50 file output thành `output.zip` chuẩn gốc, loại bỏ sự cố lỗi rỗng và cấu trúc thư mục dư thừa.

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ----- |
| **Input** | Hồ sơ khiếu nại JSON chứa `case_id`, `claimed_order_id`, chuỗi lời khiếu nại bằng tiếng Việt và hệ thống cơ sở dữ liệu bán hàng Olist dạng CSV. |
| **Output** | Bản ghi JSON chuẩn tại thư mục `output/` (tách thành các object: `assessment`, `affected_entities`, `root_cause_analysis`, `evidence_ids`, `financial_resolution`, `resolution_actions`) và file log `trace.jsonl`. |
| **Module phụ thuộc** | `src/data_loader.py` (tải CSV vào RAM) và `OllamaClient` (giao tiếp LLM trích xuất Intent với timeout 5.0s, model <= 10B). |
| **Module sử dụng output** | Bộ hệ thống đánh giá chấm điểm benchmark theo trọng số, giao tiếp với file `output.zip` thành phẩm. |
| **Điều kiện lỗi cần xử lý** | Trường hợp thiếu mã đơn hàng trong CSDL, đơn hàng rỗng (0 items đối với `unavailable`), không kết nối được Ollama (fallback lập tức sang Rule Intent), sai lệch số liệu trong chi trả (sai số cho phép $\le 0.10$ BRL). |

### Cách xác minh

```bash
.venv/bin/python main.py
.venv/bin/python scratch/validate_50_cases_schema.py
```

- **Kết quả mong đợi:** Toàn bộ 50 case của bộ test chạy mượt mà, cập nhật metadata, đóng gói 50 file JSON vào `output.zip` và kiểm thử tự động trả về báo cáo 100% hợp lệ.
- **Kết quả thực tế:** 
  + Hệ thống khởi tạo và thi hành trong ~1.5 giây; xuất log 300 sự kiện handoff vào `trace.jsonl`. Script kiểm tra hoàn trả: `ALL 50 OUTPUT JSONs PASSED SCHEMA VERIFICATION 100% PERFECTLY!`.
  + **Kết quả chấm thi Benchmark thành phần đạt `94.5850` điểm**, trong đó nổi bật là **Tài chính (`95.9877`)** và **Hành động Xử lý (`95.4870`)**, chứng minh các quy tắc đối soát và làm tròn tài chính phát huy hiệu quả thực chiến ở mức độ cực cao.
- **Artifact/log:** File thành phẩm tại `output/`, log tiến trình `logging/trace.jsonl`, metadata `logging/metadata.json` và file nén `output.zip` tại thư mục gốc.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn giữa việc dùng một prompt khổng lồ cho LLM tự phân tích và sinh thẳng ra Output JSON (End-to-End LLM Generation) hay sử dụng mô hình Điều phối Nhánh (Hybrid Tool-Using Deterministic Multi-Agent State Graph) kết hợp LLM để xử lý 50 case khiếu nại trên hệ sinh thái máy tính cá nhân local.
- **Các phương án đã cân nhắc:**
  1. **Phương án 1 (End-to-End LLM Prompts):** Dùng `qwen3:8b` đọc trực tiếp CSV của đơn hàng qua Prompt và tự xuất ra toàn bộ cú pháp JSON giải quyết khiếu nại.
  2. **Phương án 2 (Hybrid Deterministic Multi-Agent Workflow):** Phân nhiệm rành mạch: LLM chỉ thi hành nhiệm vụ đọc hiểu ý định tiếng Việt từ khiếu nại ở `CoordinatorAgent`; toàn bộ các tính toán tài chính, so sánh thời gian giao hàng và ra phán quyết theo `EC_POLICY_V1` được giao cho các Agent chuỗi (`OrderAgent`, `DeliveryAgent`, `PaymentAgent`, `PolicyAgent`, `VerifierAgent`) thực thi qua mã quy tắc mang tính tiền định (deterministic engine) và Tool chuyên dụng.
- **Phương án đã chọn:** Phương án 2 — Hybrid Deterministic Multi-Agent Workflow.
- **Lý do:** 
  - *Trade-off về độ chính xác (Correctness):* Mô hình ngôn ngữ (LLM <= 10B) rất dễ bị ảo giác (hallucination) trong các phép tính toán cộng trừ tài chính phức tạp và so sánh chuỗi ngày tháng theo giờ/phút/giây. Việc dùng Rule/Tool giúp đạt độ chính xác số học gần như tuyệt đối.
  - *Trade-off về thời gian gian lận và tài nguyên (Cost & Speed):* Thi hành trọn vẹn LLM trên máy local cho cả quá trình đọc CSV sẽ tốn từ 2-5 phút cho 50 case và hay dính timeout. Phương án Hybrid giải quyết toàn bộ 50 case chỉ trong nhấp nháy ~1-2 giây.
  - *Tính khả dĩ tái lập (Reproducibility):* Đảm bảo mọi lượt chạy lại hệ thống đều ra kết quả 100% đồng nhất cho việc audit và kiểm định benchmark.
- **Bằng chứng quyết định phù hợp:** 
  + **Bằng chứng từ thực tế thi hành:** Hệ thống thi hành mượt mà 50/50 ca không xảy ra lỗi, trút 300 log sự kiện Handoff rõ ràng ra `trace.jsonl`.
  + **Bằng chứng từ bộ chấm Benchmark:** Điểm thành phần **Tài chính đạt `95.9877`** và **Hành động xử lý đạt `95.4870`**, chứng minh tuyệt đối quyết định loại bỏ LLM ra khỏi khâu giải toán và thay thế bằng các Agent chuyên biệt với Tool-using là hoàn toàn sáng suốt và chính xác.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Lượt kiểm định bài làm ban đầu trả về 0 điểm trên các test case bị chấm Hard Gate và bị lỗi trừ điểm ở hạng mục Evidence IDs do chứa dữ liệu không xác thực (False Positive).
- **Lệnh hoặc bước tái hiện:** Kiểm tra nội dung file JSON output được tạo ra ban đầu, quan sát mảng `evidence_ids` thấy sự hiện diện của chuỗi dư thừa `"policy:EC_POLICY_V1"`, đồng thời các tham số `responsible_party_id` cho bên nền tảng bị gán thành giá trị rỗng (`null` / `None`).
- **Nguyên nhân gốc:**
  - Quy chuẩn Mục 5 của `README.md` nghiêm cấm đưa ra bất kỳ Evidence ID nào không đúng format chuẩn; chuỗi bằng chứng về chính sách chỉ cho phép format `policy:<root_cause_code>` (ví dụ: `policy:SELLER_HANDOFF_AFTER_LIMIT`). Thêm `"policy:EC_POLICY_V1"` bị hệ thống chấm điểm tự động phạt nặng thành lỗi chứng cứ sai lệch.
  - Theo Mục 4 của đề tài, bảng định dạng đòi hỏi với Platform thì ID chịu trách nhiệm phải mang chuỗi định danh `"OLIST_PLATFORM"` và với bên Vận tải là `"LOGISTICS_PROVIDER"`, chứ không phải là kiểu dữ liệu null/rỗng.
- **Cách xử lý:**
  - Trong file `src/agents/policy_agent.py`, làm sạch hàm gán chứng cứ: loại bỏ chuỗi cứng `"policy:EC_POLICY_V1"`, chỉ gán `context.candidate_evidences.append(f"policy:{decision.cause_code}")`.
  - Tinh chỉnh lại ánh xạ trong cây quy tắc: gán `decision.responsible_party_id = "OLIST_PLATFORM"` cho đơn hủy/không sẵn sàng và `decision.responsible_party_id = "LOGISTICS_PROVIDER"` cho các lỗi giao chậm do nhà vận chuyển.
  - Xây dựng thêm script rà soát tự động bóp nghẹt mọi vi phạm schema tại `scratch/validate_50_cases_schema.py`.
- **Cách xác minh sau khi sửa:** Chạy `.venv/bin/python main.py` cùng `.venv/bin/python scratch/validate_50_cases_schema.py`, thu được kết quả toàn bộ 50 file JSON hợp lệ không còn 1 điểm yếu sai cú pháp hay dư thừa Bằng chứng.
- **Điều học được:** Khi xây dựng các hệ thống Agent tự động hướng tới môi trường Enterprise hoặc tính điểm Benchmark tự động hóa, mọi chuỗi văn bản (strings, evidence IDs, role names) cần phải được khớp nối chặt chẽ theo Hợp đồng Nghiệp vụ (Business Contract / Schema Spec) đến từ ký tự, và phải luôn đi kèm với một màng lọc kiểm định (Validator layer) độc lập trước chốt hạ đầu ra.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. **Một case đi từ input JSON qua các agent đến output JSON như thế nào?**
   - Bắt đầu, `CoordinatorAgent` tiếp nhận hồ sơ khiếu nại JSON, nhờ tới mô hình LLM local (được giới hạn $\le$ 10B parameters thông qua `OllamaClient`) đọc tin nhắn tiếng Việt của khách hàng để tóm tắt và xác định Ý định Khiếu nại (Intent extraction). Sau đó Coordinator bàn giao `DisputeContext` cho `OrderAgent` để đọc thông tin đơn hàng & nhà bán từ tập CSV Olist; chuyển qua `DeliveryAgent` dùng công cụ (`DeliveryAuditTool`) kiểm định chuỗi thời gian giao - gửi và các mốc trễ hẹn; tiếp đến `PaymentAgent` đối soát tổng chi tiêu và chi trả. Sau khi quy tụ đủ bối cảnh, `PolicyAgent` thi hành ánh xạ 6 điều luật `EC_POLICY_V1` để đưa ra ra quyết định phán xét chính thức. Cuối cùng, `VerifierAgent` rà soát toàn vẹn mọi chữ số thập phân (`ROUND_HALF_UP`), tinh lọc mảng Evidence IDs theo chuẩn, chốt đơn ghi log 100% vào `output/{case_id}.json` và ghi lại chi tiết các nhịp chuyển giao vào log `trace.jsonl`.

2. **Order, item, seller và payment được join bằng những khóa nào?**
   - Các bộ dữ liệu được liên kết nhịp nhàng qua quan hệ khóa ngoại (Foreign Keys):
     - Dữ liệu đơn hàng (`order_id`) liên kết trực tiếp với bảng chi tiết món hàng (`order_items.csv`) và bảng lịch sử thanh toán (`order_payments.csv`) thông qua khóa chính **`order_id`**.
     - Trong bảng chi tiết món hàng, từng đơn vị linh kiện được định danh qua **`order_item_id`** và liên kết đến bảng thông tin người bán (`sellers.csv`) thông qua khóa **`seller_id`**.
     - Trong bảng thanh toán, các phương thức trả tiền (ví dụ chia nhỏ trả góp/thẻ/voucher) được nhận diện bằng bộ khóa ghép giữa `order_id` và **`payment_sequential`**.

3. **DeliveryAgent phân biệt lỗi seller với lỗi logistics bằng các timestamp nào?**
   - `DeliveryAgent` so sánh 4 cột mốc thời gian tối quan trọng:
     - **`order_delivered_customer_date`** (Ngày khách nhận) và **`order_estimated_delivery_date`** (Ngày dự kiến giao): Nếu `delivered_customer_date > estimated_delivery_date` (hoặc quá thời điểm khiếu nại đối với đơn chưa giao), đơn hàng bị xác định là **Giao trễ**.
     - Để tìm ra ai chịu trách nhiệm, Agent tiếp tục đem so sánh **`order_delivered_carrier_date`** (Ngày nhà bán đưa hàng cho shipper) với mốc **`shipping_limit_date`** (Hạn chót nhà bán phải giao):
       + Nếu `order_delivered_carrier_date > shipping_limit_date`: Lỗi thuộc về **Nhà bán (Seller)** do bàn giao kiện hàng quá hạn chót cho hãng vận tải.
       + Nếu `order_delivered_carrier_date` nằm bên trong hạn chót `shipping_limit_date` (nhà bán đúng hẹn): Lỗi hoàn toàn thuộc về **Đơn vị vận chuyển (Logistics Provider)** do vận chuyển chậm trễ trên đường bộ.

4. **PolicyAgent áp dụng sáu rule của `EC_POLICY_V1` theo thứ tự ưu tiên ra sao?**
   - Nắm giữ tinh thần trọng tài, `PolicyAgent` thụ lý các tình huống theo thang đo ưu tiên giảm dần tuyệt đối:
     1. **`canceled_order_paid`** (Ưu tiên 1): Đơn hàng có trạng thái `canceled` và số tiền đã thanh toán $>0$ $\rightarrow$ Trách nhiệm `platform` (`OLIST_PLATFORM`), hoàn trả toàn bộ (`issue_full_refund`).
     2. **`unavailable_order_paid`** (Ưu tiên 2): Đơn hàng ở trạng thái `unavailable` và số tiền $>0$ $\rightarrow$ Trách nhiệm `platform` (`OLIST_PLATFORM`), hoàn trả toàn bộ.
     3. **`late_delivery_seller`** (Ưu tiên 3): Đơn hàng xác minh giao trễ và người bán giao cho shipper muộn hơn hạn mức $\rightarrow$ Trách nhiệm `seller` (`<seller_id>`), phán quyết hoàn 100% cước phí vận chuyển (`refund_freight`).
     4. **`late_delivery_logistics`** (Ưu tiên 4): Đơn hàng giao trễ nhưng người bán đã bàn giao cho shipper đúng hạn $\rightarrow$ Trách nhiệm `logistics_provider` (`LOGISTICS_PROVIDER`), hoàn phí vận chuyển.
     5. **`valid_split_payment`** (Ưu tiên 5): Chỉ kích hoạt khi đơn hàng giao **đúng hạn**, sở hữu từ 2 dòng thanh toán trở lên (`payment_sequential` $\ge 2$) và tổng số tiền thanh toán khớp với tổng hóa đơn hàng + phí ship (sai số cho phép $\le 0.10$ BRL) $\rightarrow$ Không có bên vi phạm, thực hiện giải thích (`explain_valid_split_payment`).
     6. **`unsupported_late_claim`** (Ưu tiên 6/Mặc định): Các khiếu nại vô căn cứ khi giao dịch đúng hạn và thanh toán khớp, hoặc lỗi không thuộc chính sách bảo trợ $\rightarrow$ Bác bỏ khiếu nại hoàn tiền (`reject_late_refund`).

5. **VerifierAgent kiểm tra decision, evidence ID và financial resolution như thế nào trước khi ghi output?**
   - Bước cuối cùng trước khi ký tặc, `VerifierAgent` thực hiện chiến dịch kiểm toán toàn vẹn (Active Quality Audit):
     - **Kiểm định Quyết định (Decision Validation):** Soạn ra ma trận đối chiếu. Cảnh báo và đánh dấu kích hoạt cờ `verification_failed` nếu phán quyết hoàn tiền toàn bộ (`issue_full_refund`) lại mang giá trị số tiền đề xuất hoàn là $0.0$, hoặc trường `confidence` nằm ngoài dải tiêu chuẩn $[0, 1]$.
     - **Kiểm định Tài chính (Financial Resolution):** Dùng bộ đệm `decimal.Decimal` áp dụng chính xác thuật toán làm tròn `ROUND_HALF_UP` về 2 chữ số thập phân cho các chỉ tiêu `item_total_brl`, `freight_total_brl`, `payment_total_brl`, và `recommended_refund_brl`; cam kết không có sai lệch lẻ phẩy động. Nếu đơn rỗng, tự động lót 0.00 cho hàng hóa và phí ship.
     - **Kiểm định & Trộn Tinh Lọc Evidence IDs:** Đẩy toàn bộ `candidate_evidences` qua pipeline của `EvidenceBuilder`: rà soát tiền tố chuẩn xác (`order:`, `item:`, `payment:`, `seller:`, `policy:`), lọc bỏ trùng lặp (dedup), tái sắp xếp thẳng hàng theo quy ước hệ thống và khắt khe giữ nguyên giới hạn tối đa 5 ID cho mỗi nhóm thực thể bị ảnh hưởng và tối đa 10 Evidence IDs. Sau khi hợp lệ tuyệt đối 100%, mới trút xuất bản ghi ra tệp `.json`.

## 8. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Văn Hiệu  
**Ngày xác nhận:** 2026-08-05
