# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Học viên K4
**Nhóm:** K4 E-Commerce
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần nhau, cho thấy hai đoạn văn bản có nội dung hoặc ý nghĩa ngữ nghĩa tương tự, dù chúng có thể sử dụng từ ngữ khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Tôi muốn đổi lại sản phẩm vì hàng bị lỗi.
- Câu B: Sản phẩm bị hỏng nên tôi muốn yêu cầu trả hàng.
- Tại sao tương đồng: Hai câu dùng từ khác nhau nhưng đều diễn đạt cùng một ý định là trả lại sản phẩm do sản phẩm có lỗi.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Tôi muốn đổi lại sản phẩm vì hàng bị lỗi.
- Câu B: Thời tiết hôm nay khá mát và có mưa nhẹ.
- Tại sao khác: Hai câu thuộc hai chủ đề gần như không liên quan; câu đầu nói về đổi trả hàng, còn câu sau nói về thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào hướng của vector, tức là mẫu ngữ nghĩa, thay vì độ lớn tuyệt đối của vector. Với text embedding, độ dài hoặc chuẩn của vector có thể thay đổi nhưng ý nghĩa vẫn tương tự, nên cosine thường phản ánh mức độ liên quan ngữ nghĩa tốt hơn khoảng cách Euclid.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`.
> Đáp án: **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, bước nhảy giảm từ 450 xuống 400 ký tự, nên số chunk tăng lên: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25`. Overlap lớn hơn giúp giữ lại ngữ cảnh ở ranh giới giữa các chunk và giảm nguy cơ tách mất một ý quan trọng, nhưng làm tăng số lượng chunk, dung lượng lưu trữ, thời gian embedding và chi phí truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng biểu thức chính quy `re.split(r"(?<=[.!?])\s+", text)` để tách các câu dựa trên dấu chấm, dấu chấm cảm hoặc dấu hỏi theo sau bởi khoảng trắng. Cách này bảo toàn dấu câu ở cuối mỗi câu và không tạo ra mảnh câu vụn. Các câu rỗng được lọc bỏ bằng `.strip()`, sau đó nhóm thành các khối có tối đa `max_sentences_per_chunk` câu ghép lại bằng một khoảng trắng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy duyệt qua danh sách dấu phân cách theo thứ tự ưu tiên giảm dần: đoạn văn (`\n\n`), dòng (`\n`), câu (`. `), từ (` `), và ký tự (`""`). Base case 1 dừng khi độ dài văn bản nhỏ hơn `chunk_size`. Base case 2 chia theo kích thước cố định khi hết phân cách. Nếu separator xuất hiện, văn bản được tách và gộp lại liên tục sao cho tổng độ dài mỗi chunk không vượt quá `chunk_size`; mảnh nào quá lớn sẽ được đệ quy với separator cấp thấp hơn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Trong bộ nhớ `self._store`, tôi lưu các bản ghi dưới dạng dict gồm `id`, `content`, `metadata` (bản sao), và `embedding`. Lớp `_search_records` thực hiện tính tích vô hướng (`_dot`) giữa vector query và vector từng record trong một vòng lặp duy nhất, sau đó sắp xếp kết quả theo điểm `score` giảm dần và cắt lấy `top_k` kết quả hàng đầu.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện lọc (filter) trước bằng cách kiểm tra tất cả các cặp key-value trong `metadata_filter` phải trùng khớp với `metadata` của record, rồi mới đưa danh sách đã lọc vào `_search_records` để xếp hạng (tránh bị mất kết quả phù hợp). `delete_document` loại bỏ toàn bộ record có `metadata['doc_id'] == doc_id` và trả về `True` nếu có ít nhất một bản ghi bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tác tử gọi `self.store.search(question, top_k=top_k)` để lấy các chunk liên quan nhất. Ngữ cảnh được inject vào Prompt dưới dạng đánh số `[1]`, `[2]` kèm theo `doc_id` của file nguồn để đảm bảo tính grounding. Prompt đưa ra chỉ dẫn rõ ràng yêu cầu LLM chỉ sử dụng ngữ cảnh được cung cấp để trả lời và thông báo rõ nếu thông tin không đủ.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-8.3.4, pluggy-1.5.0 -- C:\Users\Admin\anaconda3\python.exe
cachedir: .pytest_cache
rootdir: D:\AI20K\K4-Day07-Gehihi36
plugins: anyio-4.7.0
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.09s ==============================
```

**Số lượng bài test vượt qua (pass):** **42** / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách đổi trả hàng Shopee | Quy định hoàn tiền sản phẩm bị lỗi | cao | 0.85 | Đúng |
| 2 | Phương thức thanh toán qua ShopeePay | Hướng dẫn sử dụng ví ShopeePay | cao | 0.88 | Đúng |
| 3 | Cách theo dõi vận chuyển đơn hàng | Điều khoản dịch vụ cho người bán | thấp | 0.22 | Đúng |
| 4 | Quy trình khiếu nại sản phẩm bể vỡ | Thời tiết hôm nay có mưa lớn | thấp | 0.05 | Đúng |
| 5 | Hạn mức trả hàng COM cho khách Kim Cương | Ưu đãi hạng thành viên VIP Shopee | cao | 0.76 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả ấn tượng nhất là Cặp 1 ("Chính sách đổi trả hàng Shopee" và "Quy định hoàn tiền sản phẩm bị lỗi") đạt điểm tương tự 0.85 mặc dù không dùng chung từ khóa chính. Điều này khẳng định rằng text embeddings biểu diễn ngữ nghĩa của cả câu trong không gian không gian nhiều chiều (semantic space) dựa trên ý định thực sự của người dùng chứ không chỉ dựa vào trùng khớp từ khóa bề mặt (lexical matching).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua phải gửi yêu cầu trả hàng hoàn tiền trong bao lâu với thực phẩm tươi sống và với các sản phẩm còn lại? | `shopee-return-refund-policy` (chunk 6): Gửi yêu cầu trả hàng trong vòng 15 ngày kể từ lúc đơn hàng giao thành công (24h với thực phẩm tươi sống). | 0.887 | Có | Thực phẩm tươi sống/đông lạnh: 24 giờ kể từ khi giao thành công; các sản phẩm còn lại: 15 ngày. |
| 2 | Lý do đổi ý khi sản phẩm còn nguyên tem nhãn mác bao bì áp dụng cho nhóm người mua nào và ngoại trừ những loại nào? | `shopee-general-return-refund-rules` (chunk 7): Điều kiện trả hàng hoàn tiền của Shopee: Khác với mô tả và Đổi ý sản phẩm còn nguyên tem/nhãn/mác/hộp. | 0.545 | Có | Điều kiện áp dụng cho sản phẩm còn nguyên tem/nhãn/mác và hộp của nhà sản xuất (ngoại trừ các sản phẩm hạn chế). |
| 3 | Khi hệ thống ghi nhận đã trả hàng thành công nhưng Shop chưa nhận được hàng hoặc hàng hoàn gặp vấn đề thì phải phản hồi khi nào và hạn phản hồi là bao lâu? | `shopee-seller-manage-return-refund` (chunk 6): Hướng dẫn phản hồi đến Shopee khi chưa nhận được hàng hoàn hoặc hàng hoàn gặp vấn đề. | 0.687 | Có | Shop phản hồi từ ngày hệ thống ghi nhận trả hàng thành công; hạn phản hồi là trong vòng 02 ngày. |
| 4 | Thời gian nhận tiền hoàn qua Ví ShopeePay, thẻ nội địa Napas, thẻ tín dụng ghi nợ và SPayLater là bao lâu? | `shopee-refund-time-status` (chunk 6): Lưu ý xử lý hoàn tiền về Ví ShopeePay (trong 24h) và các phương thức thanh toán trả góp SPayLater. | 0.711 | Có | Thời gian nhận hoàn tiền qua Ví ShopeePay là trong vòng 24h (nếu tài khoản bình thường và liên kết hợp lệ). |
| 5 | Nếu thanh toán báo lỗi M10 vượt hạn mức thanh toán trong ngày thì Shopee hướng dẫn xử lý thế nào? | `shopee-card-payment-errors` (chunk 4): Hướng dẫn xử lý khi thanh toán thẻ chưa hoàn tất hoặc gặp lỗi thanh toán. | 0.535 | Có | Hướng dẫn liên hệ ngân hàng phát hành thẻ hoặc hỗ trợ Shopee để kiểm tra trạng thái thanh toán. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5** / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua quá trình làm việc nhóm, tôi học được rằng bước làm sạch dữ liệu HTML (đặc biệt là chuyển đổi cấu trúc bảng `<table>` thành Markdown Table) có ảnh hưởng quyết định đến chất lượng của Vector Search. Nếu để bảng bị vỡ thành các dòng từ đơn lẻ, Embedding Store sẽ không thể truy xuất đúng ngữ cảnh của tiêu chí so sánh.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
