# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                     |
| --------------- | -------------------------------------------- |
| Họ và tên       | Đỗ Ngọc Anh                                  |
| MSSV            | 2A202601343                                  |
| Khóa/Lớp        | K3                                           |
| Vai trò chính   | Full Pipeline Developer (Multi-Agent System) |
| Ngày hoàn thành | 2026-08-05                                   |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable   | File/hàm phụ trách                                           | Input nhận vào                                  | Output bàn giao                                                                                      | Trạng thái |
| -------------------- | ------------------------------------------------------------ | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------- |
| Data Access Layer    | `src/data_access/loader.py`, `src/data_access/repository.py` | Bộ dữ liệu Olist (CSV), `order_id`              | Cung cấp dữ liệu order, item, payment và seller cho các agent thông qua Repository Pattern           | Hoàn thành |
| Domain Models        | `src/models/*`                                               | Dữ liệu từ Repository                           | Chuẩn hóa dữ liệu trao đổi giữa các agent bằng dataclass                                             | Hoàn thành |
| Business Rule Engine | `src/rules/business_rules.py`                                | Order, Items, Payments                          | Xác định primary issue, refund, root cause, responsible party và resolution action theo EC_POLICY_V1 | Hoàn thành |
| Multi-Agent System   | `src/agents/*`                                               | `order_id`                                      | Thu thập thông tin theo từng domain (Order, Payment, Delivery, Policy, Verification)                 | Hoàn thành |
| Coordinator          | `src/coordinator/coordinator.py`                             | `order_id`                                      | Điều phối workflow giữa các agent và tổng hợp kết quả                                                | Hoàn thành |
| Output Builder       | `src/output/output_builder.py`                               | `CaseResult`, `payments`, `case_id`, `order_id` | Chuyển kết quả nội bộ thành JSON đúng schema yêu cầu                                                 | Hoàn thành |
| Main Pipeline        | `main.py`                                                    | 50 file JSON trong thư mục `input/`             | Xử lý toàn bộ input, sinh 50 file output JSON, `trace.jsonl` và `metadata.json`                      | Hoàn thành |

Tôi chịu trách nhiệm thiết kế và triển khai toàn bộ hệ thống Multi-Agent cho bài toán E-commerce Dispute Resolution. Hệ thống được tổ chức theo kiến trúc phân tách trách nhiệm, trong đó mỗi agent xử lý một domain dữ liệu riêng, Coordinator điều phối quá trình handoff và Output Builder chuyển đổi kết quả nội bộ sang đúng định dạng output theo yêu cầu của đề bài. Toàn bộ pipeline hoạt động end-to-end từ Input JSON đến Output JSON.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động         | Thành viên/module được hỗ trợ | Kết quả                                                                                                                                                                |
| ----------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Kiểm thử và debug | Toàn bộ hệ thống              | Kiểm thử từng module độc lập (Repository, Business Rules, Agents, Coordinator, Output Builder) và kiểm thử end-to-end thông qua `main.py`.                             |
| Tối ưu tích hợp   | Pipeline xử lý                | Khắc phục lỗi import, lỗi truy xuất dữ liệu, lỗi ghi đè output, lỗi sinh evidence IDs và đảm bảo hệ thống tạo thành công 50 file output JSON theo đúng schema yêu cầu. |
| Xác minh kết quả  | Output và Trace               | Kiểm tra output JSON, `trace.jsonl` và `metadata.json`, xác nhận pipeline chạy thành công trên toàn bộ bộ dữ liệu đầu vào.                                             |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện                                   | File/hàm/artifact liên quan                                    | Kết quả bàn giao                                                            | Cách xác minh                                         |
| ------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------- |
| Xây dựng tầng truy xuất dữ liệu và Business Rule Engine | `src/data_access/*`, `src/rules/business_rules.py`             | Repository Pattern và Business Rule Engine hoạt động đúng theo EC_POLICY_V1 | Chạy các script kiểm thử Repository và Business Rules |
| Xây dựng pipeline Multi-Agent và sinh output            | `src/agents/*`, `src/coordinator/*`, `src/output/*`, `main.py` | Sinh thành công 50 file JSON, `trace.jsonl` và `metadata.json`              | Chạy `python main.py` và kiểm tra thư mục `output/`   |

Một artifact cụ thể được tạo ra là thư mục `output/` chứa 50 file JSON đúng schema yêu cầu của đề bài, cùng với `trace.jsonl` ghi lại quá trình xử lý và `metadata.json` mô tả cấu hình hệ thống.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Xây dựng một hệ thống Multi-Agent có khả năng đọc dữ liệu từ nhiều bảng CSV của Olist, tổng hợp thông tin theo từng domain, áp dụng business rules trong EC_POLICY_V1 và sinh kết quả theo đúng output schema của đề bài.

### Cách triển khai

Hệ thống được xây dựng theo kiến trúc phân tầng. DataLoader chịu trách nhiệm nạp dữ liệu một lần từ các file CSV. Repository Pattern cung cấp các hàm truy xuất dữ liệu theo `order_id`. Mỗi Agent xử lý một domain dữ liệu riêng (Order, Payment, Delivery), sau đó Coordinator điều phối việc thực thi và chuyển kết quả cho Policy Agent để áp dụng business rules. Verifier Agent kiểm tra kết quả cuối cùng trước khi Output Builder chuyển đổi thành JSON đúng schema.

### Input, output và contract

| Thành phần              | Mô tả                                                                                                   |
| ----------------------- | ------------------------------------------------------------------------------------------------------- |
| Input                   | File JSON trong thư mục `input/` chứa `case_id` và `claimed_order_id`                                   |
| Output                  | File JSON trong thư mục `output/` theo đúng schema của đề bài                                           |
| Module phụ thuộc        | `loader.py`, `repository.py`, `business_rules.py`                                                       |
| Module sử dụng output   | `Coordinator`, `OutputBuilder`, `main.py`                                                               |
| Điều kiện lỗi cần xử lý | Order không tồn tại, order không có item, nhiều payment rows, dữ liệu thời gian thiếu hoặc không hợp lệ |

### Cách xác minh

```bash
python main.py
```

* **Kết quả mong đợi:** Hệ thống xử lý toàn bộ các file trong thư mục `input/` và sinh đầy đủ output.
* **Kết quả thực tế:** Hệ thống sinh thành công 50 file JSON trong thư mục `output/`, đồng thời tạo `trace.jsonl` và `metadata.json`.
* **Artifact/log:** `output/`, `trace.jsonl`, `metadata.json`.

## 5. Một quyết định kỹ thuật quan trọng

* **Bối cảnh:** Bài toán yêu cầu xây dựng hệ thống Multi-Agent để giải quyết tranh chấp đơn hàng dựa trên dữ liệu Olist và bộ quy tắc EC_POLICY_V1. Tôi cần lựa chọn giữa việc sử dụng LLM để suy luận hoặc xây dựng hệ thống Rule-based.

* **Các phương án đã cân nhắc:**

  1. Sử dụng LLM để phân tích và đưa ra quyết định.
  2. Xây dựng Business Rule Engine theo đúng EC_POLICY_V1 và tổ chức thành hệ thống Multi-Agent.

* **Phương án đã chọn:** Xây dựng hệ thống Rule-based Multi-Agent.

* **Lý do:** Các quy tắc nghiệp vụ trong đề bài đã được định nghĩa rõ ràng và có thể kiểm chứng trực tiếp từ dữ liệu CSV. Việc sử dụng Rule-based giúp kết quả mang tính xác định (deterministic), dễ kiểm thử, dễ debug và tránh hiện tượng hallucination của mô hình ngôn ngữ. Đồng thời hệ thống không phụ thuộc vào API hay mô hình có kích thước lớn, phù hợp với yêu cầu của bài lab.

* **Bằng chứng quyết định phù hợp:** Hệ thống xử lý thành công toàn bộ 50 case, sinh đúng output theo schema yêu cầu, đồng thời tạo đầy đủ `trace.jsonl` và `metadata.json`. Pipeline hoạt động ổn định mà không cần sử dụng mô hình ngôn ngữ.

## 6. Một lỗi hoặc blocker đã xử lý

* **Triệu chứng/lỗi nguyên văn:** Kết quả `payment_total` và `evidence_ids` trong output JSON không khớp với dữ liệu thực tế của đơn hàng.

* **Lệnh hoặc bước tái hiện:**

```bash
python -m scripts.test_output_builder
python main.py
```

* **Nguyên nhân gốc:** Logic tổng hợp payment và sinh evidence IDs chưa xử lý đúng dữ liệu từ Repository. Một số payment ID và evidence ID được tạo cứng hoặc chưa lấy trực tiếp từ dữ liệu thực tế, dẫn đến output không đúng schema mong muốn.

* **Cách xử lý:** Rà soát lại Repository, Payment Agent và Output Builder; lấy toàn bộ payment information trực tiếp từ dữ liệu CSV, sinh `payment_ids` và `evidence_ids` theo đúng định dạng yêu cầu của đề bài thay vì sử dụng giá trị cố định.

* **Cách xác minh sau khi sửa:** Chạy lại toàn bộ các script kiểm thử và thực thi `main.py`. Kiểm tra output JSON và đối chiếu với dữ liệu gốc trong Olist.

* **Điều học được:** Khi xây dựng hệ thống Multi-Agent, việc chuẩn hóa dữ liệu giữa các agent và đảm bảo mỗi agent chỉ sử dụng dữ liệu đã được xác minh từ Repository giúp giảm lỗi tích hợp và tăng tính nhất quán của toàn bộ pipeline.

## 7. Hiểu biết về luồng end-to-end

**1. Dữ liệu đi từ Crossref đến vector index như thế nào?**

Metadata và tài liệu được thu thập từ Crossref, sau đó được làm sạch, chia thành các đoạn (chunking), chuyển thành embedding bằng embedding model và lưu vào vector index để phục vụ truy xuất ngữ nghĩa.

---

**2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**

Evaluation set là tập câu hỏi dùng để đánh giá hệ thống. Ground-truth document IDs là các tài liệu đúng tương ứng với từng câu hỏi. So sánh kết quả retrieval với ground-truth giúp đo chất lượng truy xuất, sau đó mới đánh giá chất lượng câu trả lời của hệ thống.

---

**3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?**

Quality checks đánh giá tính đúng đắn, đầy đủ và nhất quán của dữ liệu hoặc kết quả truy xuất. Freshness monitoring theo dõi dữ liệu mới hoặc dữ liệu đã thay đổi để đảm bảo hệ thống luôn sử dụng thông tin cập nhật.

---

**4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**

Sử dụng cùng một test set giúp đảm bảo việc so sánh là công bằng. Mọi thay đổi về metric đều phản ánh chất lượng của hệ thống sau khi sửa, không bị ảnh hưởng bởi sự khác biệt của dữ liệu kiểm thử.

---

**5. Repair được xem là thành công dựa trên artifact và metric nào?**

Repair được xem là thành công khi artifact được tạo đúng quy trình (vector index, log, output hoặc report) và các metric đánh giá như Recall@K, Precision@K hoặc Answer Accuracy được cải thiện so với baseline mà không làm giảm tính ổn định của hệ thống.

## 8. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đỗ Ngọc Anh
**Ngày xác nhận:** 2026-08-05
