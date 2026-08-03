# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Dũng
**Nhóm:** Gehihi36
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai đoạn văn bản có độ tương tự cosine cao nghĩa là các vector embedding của chúng trỏ về cùng một hướng trong không gian vector, phản ánh rằng hai đoạn văn bản đó có nội dung hoặc ý nghĩa tương đồng nhau. Điểm cosine gần 1.0 có nghĩa là hai văn bản gần như đồng nghĩa hoặc bàn về cùng chủ đề theo cách tương tự.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Làm thế nào để đổi trả hàng đã mua?"
- Câu B: "Chính sách hoàn trả sản phẩm là gì?"
- Tại sao tương đồng: Cả hai câu đều hỏi về quy trình hoàn/đổi hàng hóa — cùng chủ đề, cùng ý định người dùng (user intent), chỉ khác cách diễn đạt.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Phí vận chuyển được tính như thế nào?"
- Câu B: "Điều khoản bảo mật dữ liệu cá nhân của người bán."
- Tại sao khác: Một câu nói về logistics/phí ship, câu kia nói về quyền riêng tư pháp lý — hai chủ đề hoàn toàn khác nhau trong không gian ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng bởi độ dài (magnitude) của vector, tức là một văn bản dài hơn sẽ có vector "to" hơn và bị coi là "xa" hơn dù nội dung giống nhau. Cosine similarity chỉ đo góc giữa các vector, bỏ qua độ lớn, nên nó phản ánh đúng sự tương đồng về ý nghĩa bất kể độ dài văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính theo công thức:
> ```
> số chunk = ceil((độ_dài - overlap) / (chunk_size - overlap))
>           = ceil((10000 - 50) / (500 - 50))
>           = ceil(9950 / 450)
>           = ceil(22.11)
>           = 23 chunks
> ```
> **Đáp án: 23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Với overlap=100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks` — tức là tăng thêm 2 chunks. Ta muốn overlap nhiều hơn để đảm bảo thông tin quan trọng nằm ở ranh giới giữa hai chunk không bị cắt đứt ngữ cảnh, giúp retrieval chính xác hơn khi câu trả lời nằm ở vùng tiếp giáp giữa hai đoạn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng `re.split(r"(?<=[.!?]) (?=\S)|(?<=\.)\n", text)` để tách câu theo các ký tự kết thúc (`.`, `!`, `?`) theo sau bởi khoảng trắng hoặc xuống dòng, đồng thời giữ dấu câu gắn với câu trước (lookbehind). Sau khi lọc các chuỗi rỗng và strip whitespace, tôi nhóm các câu lại theo từng batch `max_sentences_per_chunk` bằng cách bước qua list với stride đúng bằng kích thước nhóm. Edge case được xử lý: empty text trả về `[]`, max_sentences_per_chunk được clamp tối thiểu là 1.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động đệ quy: bắt đầu từ danh sách separators theo thứ tự ưu tiên (paragraph → newline → sentence → word → character). Base case là khi `len(text) <= chunk_size` thì trả về `[text]`, hoặc khi không còn separator nào thì hard-split theo kích thước. Với mỗi separator, tôi split text thành các phần, sau đó dùng một buffer để ghép các phần nhỏ lại thành chunk vừa đủ, khi phần quá lớn thì gọi đệ quy `_split` với danh sách separator còn lại.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Với `add_documents`, tôi dùng hàm `_make_record` để build một record chuẩn hóa (gán unique ID dạng `doc_id::index`, embed content, attach metadata), rồi append vào `self._store` (in-memory). Nếu ChromaDB khả dụng thì cũng add song song vào collection, nhưng luôn giữ bản copy in-memory để đảm bảo tính nhất quán. `search` embed query rồi tính dot product với tất cả embedding đã lưu, sort descending và trả về top_k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc **trước** bằng cách filter `self._store` theo `metadata_filter` (tất cả key-value phải match), sau đó chạy `_search_records` trên tập candidates đã lọc. `delete_document` tìm tất cả record có `metadata['doc_id'] == doc_id`, xóa khỏi ChromaDB nếu dùng, rồi filter lại `self._store`. Trả về `True` nếu có record bị xóa (size giảm), `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tôi implement theo đúng pattern RAG 3 bước: (1) gọi `self._store.search(question, top_k)` để lấy các chunk liên quan nhất; (2) format context bằng cách join các chunk với số thứ tự `[1] content`, `[2] content`...; (3) build prompt với instruction rõ ràng yêu cầu LLM chỉ trả lời dựa vào context (grounding), sau đó gọi `self._llm_fn(prompt)`. Nếu không có context, inject `"(no relevant context found)"` để LLM biết và không đoán mò.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform darwin -- Python 3.11.14, pytest-9.1.1, pluggy-1.6.0
collected 42 items

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

============================== 42 passed in 0.05s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Chính sách đổi trả hàng hóa" | "Hướng dẫn hoàn tiền khi trả hàng" | cao | 0.72 | ✅ |
| 2 | "Phí vận chuyển tính theo km" | "Bảo mật dữ liệu người dùng" | thấp | 0.08 | ✅ |
| 3 | "Thời gian giao hàng dự kiến" | "Estimated delivery time" | cao | 0.65 | ✅ |
| 4 | "Điều kiện để trở thành người bán" | "Thanh toán bằng ví điện tử" | thấp | 0.21 | ✅ |
| 5 | "Làm thế nào để hủy đơn hàng?" | "Cách cancel order đã đặt?" | cao | 0.81 | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 3 ("Thời gian giao hàng dự kiến" vs "Estimated delivery time") có điểm khá cao (0.65) dù một câu tiếng Việt và một câu tiếng Anh — điều này cho thấy model multilingual embedding đã học được ánh xạ ngữ nghĩa xuyên ngôn ngữ. Điều ngạc nhiên hơn là cặp 5 (hỏi hủy đơn theo hai cách khác nhau) có điểm cao nhất (0.81), chứng tỏ embeddings nắm bắt user intent tốt hơn là từ ngữ bề mặt — đây chính là sức mạnh cốt lõi của semantic search so với keyword matching.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Chính sách đổi trả hàng bị lỗi như thế nào? | Chunk về quy trình đổi trả: "Sản phẩm lỗi được đổi trong 7 ngày..." | 0.74 | ✅ Có | Khách hàng có thể đổi/trả trong 7 ngày nếu sản phẩm bị lỗi do nhà sản xuất. |
| 2 | Phí vận chuyển được tính như thế nào? | Chunk về phí ship: "Phí vận chuyển tính theo khoảng cách và trọng lượng..." | 0.69 | ✅ Có | Phí ship dựa trên khoảng cách giao hàng và trọng lượng kiện hàng. |
| 3 | Người bán cần đáp ứng điều kiện gì? | Chunk về điều kiện người bán: "Người bán phải cung cấp CMND/CCCD và tài khoản ngân hàng..." | 0.71 | ✅ Có | Cần có giấy tờ tùy thân hợp lệ và tài khoản ngân hàng xác minh. |
| 4 | Dữ liệu cá nhân của tôi được bảo vệ thế nào? | Chunk về chính sách bảo mật: "Thông tin cá nhân được mã hóa và không chia sẻ với bên thứ ba..." | 0.68 | ✅ Có | Dữ liệu được mã hóa SSL và không bán/chia sẻ cho bên thứ ba. |
| 5 | Thanh toán bằng ví MoMo có được không? | Chunk về phương thức thanh toán: "Hỗ trợ thanh toán qua MoMo, ZaloPay, VNPay và thẻ ngân hàng..." | 0.77 | ✅ Có | Có, hỗ trợ MoMo cùng nhiều ví điện tử và thẻ ngân hàng khác. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi nhận ra rằng chiến lược chunking theo cấu trúc tài liệu (section-based hoặc QA-based) cho kết quả retrieval tốt hơn nhiều so với fixed-size chunking đơn thuần trên dữ liệu chính sách TMĐT — vì mỗi "điều khoản" là một đơn vị ngữ nghĩa tự nhiên. Điều này giúp tôi hiểu rằng việc thiết kế chunker nên bắt đầu từ cấu trúc của dữ liệu, không phải từ con số kích thước chunk tùy ý.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |