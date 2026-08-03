# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Tuấn Đức  
**Mã sinh viên:** 2A202601380  
**Nhóm:** Gehihi36  
**Ngày:** 03/08/2026  

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity)

**Độ tương tự cosine cao nghĩa là gì?**  
Cosine similarity cao nghĩa là hai vector embedding có hướng gần nhau, tức hai đoạn văn/câu có xu hướng biểu diễn ý nghĩa gần nhau trong không gian vector. Với text retrieval, điểm cao thường là tín hiệu rằng tài liệu có liên quan về mặt ngữ nghĩa với câu hỏi.

**Ví dụ có độ tương tự cao:**

- Câu A: Người mua có thể nhận tiền hoàn qua Ví ShopeePay trong 24 giờ.
- Câu B: Tiền hoàn về Ví ShopeePay thường được xử lý trong vòng 24 giờ.
- Tại sao tương đồng: Cả hai câu cùng nói về phương thức hoàn tiền ShopeePay và cùng mốc thời gian 24 giờ.

**Ví dụ có độ tương tự thấp:**

- Câu A: Shop phải phản hồi khi hàng hoàn gặp vấn đề.
- Câu B: Người mua có thể thanh toán bằng thẻ Napas.
- Tại sao khác: Hai câu thuộc hai nghiệp vụ khác nhau: xử lý trả hàng của người bán và phương thức thanh toán của người mua.

**Vì sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**  
Cosine similarity tập trung vào hướng của vector, phù hợp hơn khi cần so ý nghĩa thay vì độ lớn tuyệt đối của vector. Với embedding văn bản, hai câu có thể dài/ngắn khác nhau nhưng vẫn cùng chủ đề, nên hướng vector thường hữu ích hơn khoảng cách Euclid thô.

### Bài toán tính toán Chunking

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

- Bước nhảy giữa hai chunk: `500 - 50 = 450`
- Chunk đầu lấy ký tự `0..499`, các chunk sau dịch thêm `450`
- Số chunk: `ceil((10000 - 500) / 450) + 1 = ceil(9500 / 450) + 1 = 22 + 1 = 23`

**Đáp án:** 23 chunks.

**Nếu overlap tăng lên 100, số lượng chunk thay đổi thế nào?**  
Khi overlap tăng lên 100, bước nhảy còn `500 - 100 = 400`, nên số chunk là `ceil((10000 - 500) / 400) + 1 = 25`. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới chunk tốt hơn, nhưng làm tăng số chunk, tăng chi phí embedding và có thể tạo thêm kết quả trùng lặp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` — hướng tiếp cận:**  
Tôi dùng regex `(?<=[.!?])\s+` để tách câu tại khoảng trắng sau các dấu kết thúc câu `.`, `!`, `?`, đồng thời giữ lại dấu câu trong từng câu. Sau đó tôi loại câu rỗng, strip khoảng trắng và gom theo `max_sentences_per_chunk`. Trường hợp input rỗng trả về list rỗng để không làm lỗi pipeline.

**`RecursiveChunker.chunk` / `_split` — hướng tiếp cận:**  
Tôi triển khai chia đệ quy theo độ ưu tiên separator: đoạn văn, dòng, câu, khoảng trắng, rồi fallback cắt fixed-size khi không còn separator phù hợp. Base case là text đã ngắn hơn `chunk_size`, hoặc không còn separator thì cắt trực tiếp theo `chunk_size`. Cách này giữ cấu trúc tự nhiên của văn bản tốt hơn fixed-size thuần.

### Lớp EmbeddingStore

**`add_documents` + `search` — hướng tiếp cận:**  
Mỗi `Document` được chuẩn hóa thành record gồm `id`, `content`, bản sao `metadata`, và `embedding` của nội dung. Với in-memory store, tôi lưu các record trong list và search bằng dot product giữa query embedding và chunk embedding, sau đó sort giảm dần theo score và lấy top-k. Với benchmark thật, tôi bổ sung tùy chọn Chroma persistent để lưu vector thật.

**`search_with_filter` + `delete_document` — hướng tiếp cận:**  
Filter được áp dụng trước khi ranking để tránh trường hợp top-k bị chiếm bởi tài liệu sai metadata rồi mới bị loại. Với in-memory, tôi lọc record bằng exact match metadata; với Chroma, tôi chuyển filter nhiều field sang `$and`. `delete_document(doc_id)` xóa mọi chunk có `metadata["doc_id"]` khớp với file gốc.

### Tác tử KnowledgeBaseAgent

**`answer` — hướng tiếp cận:**  
Agent gọi store để retrieve top-k chunk, sau đó ghép context có đánh số `[1]`, `[2]`, kèm `doc_id/source` để truy vết. Prompt yêu cầu LLM chỉ dùng context và nói rõ khi context không đủ. Tôi cũng thêm `metadata_filter` tùy chọn để agent có thể trả lời các câu cần filter như query dành cho seller.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử

Lệnh chạy:

```powershell
python -m pytest tests -v
```

Output chính:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.1.1
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::* PASSED
tests/test_solution.py::TestSentenceChunker::* PASSED
tests/test_solution.py::TestRecursiveChunker::* PASSED
tests/test_solution.py::TestEmbeddingStore::* PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::* PASSED
tests/test_solution.py::TestComputeSimilarity::* PASSED
tests/test_solution.py::TestCompareChunkingStrategies::* PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::* PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::* PASSED

======================== 42 passed, 1 warning in 0.10s ========================
```

**Số lượng bài test vượt qua:** 42 / 42

Ghi chú: warning duy nhất là pytest không ghi được `.pytest_cache` trong môi trường Windows hiện tại; warning này không ảnh hưởng logic hay kết quả test.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi dự đoán trước theo ý nghĩa tự nhiên của câu, sau đó tính điểm thực tế bằng `_mock_embed` và `compute_similarity`. Vì `MockEmbedder` deterministic nhưng không biểu diễn ngữ nghĩa thật, một số kết quả bị lệch so với trực giác.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Shopee hoàn tiền qua Ví ShopeePay trong 24 giờ. | Thời gian nhận tiền hoàn về Ví ShopeePay là 24 giờ. | cao | 0.146 | Có, nhưng điểm không cao rõ rệt |
| 2 | Người bán phải phản hồi khi hàng hoàn gặp vấn đề. | Shop cần phản hồi nếu hàng hoàn bị thiếu hoặc hư hại. | cao | -0.051 | Không |
| 3 | Lỗi M10 yêu cầu người mua đặt hàng lại ngày mai. | Người mua nên thử đặt hàng lại vào ngày tiếp theo khi gặp M10. | cao | 0.133 | Có, nhưng yếu |
| 4 | Thời gian hoàn tiền qua Napas là 2 đến 5 ngày làm việc. | Chính sách trả hàng cho thực phẩm tươi sống là 24 giờ. | thấp | 0.144 | Không |
| 5 | Điều khoản dịch vụ quy định về tài khoản người dùng. | Bảng lỗi thanh toán liệt kê mã M08 và M10. | thấp | 0.056 | Có |

**Kết quả bất ngờ nhất:**  
Cặp 2 có ý nghĩa rất gần nhau nhưng điểm mock lại âm, trong khi cặp 4 khác ý nhưng điểm dương tương đối. Điều này cho thấy mock embedding chỉ phù hợp để kiểm tra luồng kỹ thuật, không nên dùng để kết luận chất lượng retrieval ngữ nghĩa. Vì vậy phần benchmark thật của tôi dùng local multilingual embedding.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Cấu hình benchmark

- Corpus: `data/shopee_selected`
- Strategy: `HeadingAwareChunker(chunk_size=700)`
- Embedding: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Vector store: Chroma persistent
- Chroma dir: `.chroma/shopee_heading_700`
- Số chunk nạp vào store: 392

Lệnh chạy:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:EMBEDDING_PROVIDER='local'
$env:VECTOR_STORE='chroma'
$env:CHROMA_DIR='.chroma\shopee_heading_700'
$env:CHUNKER='heading'
$env:CHUNK_SIZE='700'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
conda run -n vmec-clinical-copilot python bench.py
```

### Bảng kết quả 5 query

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua phải gửi yêu cầu trả hàng hoàn tiền trong bao lâu với thực phẩm tươi sống và với các sản phẩm còn lại? | `shopee-return-refund-policy`, chunk 7: chứa mốc 15 ngày và 24 giờ cho thực phẩm tươi sống/đông lạnh. | 0.770 | Có, evidence rank 1 | Trả lời được: sản phẩm thường 15 ngày, thực phẩm tươi sống/đông lạnh 24 giờ. |
| 2 | Lý do đổi ý khi sản phẩm còn nguyên tem nhãn mác bao bì áp dụng cho nhóm người mua nào và ngoại trừ những loại nào? | `shopee-general-return-refund-rules`, chunk 7: đúng tài liệu nhưng chunk top-1 nói về điều kiện khác; chunk rank 2 mới chứa dòng `Đổi ý`. | 0.545 | Có trong top-3, nhưng top-1 chưa đủ | Trả lời cần dựa vào chunk rank 2: áp dụng cho hạng Kim Cương, Vàng, Shopee VIP; loại trừ Shopee Mart và danh sách hạn chế. |
| 3 | Khi hệ thống ghi nhận đã trả hàng thành công nhưng Shop chưa nhận được hàng hoặc hàng hoàn gặp vấn đề thì phải phản hồi khi nào và hạn phản hồi là bao lâu? | `shopee-seller-manage-return-refund`, chunk 6: bảng phản hồi của seller, có thời điểm phản hồi và hạn trong vòng 2 ngày. | 0.687 | Có, evidence rank 1 | Trả lời được: phản hồi từ ngày hệ thống cập nhật trả hàng thành công, hạn trong vòng 2 ngày. |
| 4 | Thời gian nhận tiền hoàn qua Ví ShopeePay, thẻ nội địa Napas, thẻ tín dụng ghi nợ và SPayLater là bao lâu? | `shopee-refund-time-status`, chunk 7: đúng tài liệu nhưng chỉ là phần lưu ý về Ví ShopeePay, không chứa đủ bảng Napas/thẻ tín dụng/SPayLater. | 0.711 | Không đủ evidence trong top-3 | Agent thiếu căn cứ đầy đủ để trả lời toàn bộ danh sách thời gian hoàn tiền. |
| 5 | Nếu thanh toán báo lỗi M10 vượt hạn mức thanh toán trong ngày thì Shopee hướng dẫn xử lý thế nào? | `shopee-order-payment-errors`, chunk 0: title của tài liệu lỗi thanh toán; chunk rank 2 mới chứa dòng M10 và hướng dẫn ngày mai. | 0.529 | Có trong top-3, nhưng top-1 chưa đủ | Trả lời đúng nếu dùng chunk rank 2: lỗi M10 thì đặt hàng lại vào ngày mai. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5 theo evidence chunk-level.  
**Doc hit@3:** 5 / 5.  
**Chunk-level score:** 6 / 10.

### A/B metadata filter

Query A/B: Q3, câu hỏi dành cho seller về phản hồi khi hàng hoàn gặp vấn đề.

- Có filter `{"customer_role": "seller"}`: evidence đứng rank 1, top-1 là `shopee-seller-manage-return-refund`, chunk 6.
- Không filter: evidence vẫn có nhưng rơi xuống rank 3; top-1 bị kéo sang `shopee-return-refund-policy`, chunk 23.

Kết luận: filter giúp tăng precision rõ ràng trong câu hỏi có vai trò cụ thể. Tuy nhiên, filter cũng có đánh đổi recall: nếu metadata sai hoặc câu hỏi cần thông tin trong tài liệu `both`, filter quá hẹp có thể loại nhầm tài liệu chứa đáp án.

### Failure case chính

Failure case tốt nhất là Q4. Top-3 đều thuộc đúng tài liệu `shopee-refund-time-status`, nên nếu chỉ chấm theo `doc_id` thì sẽ tưởng retrieval đúng. Nhưng các chunk retrieved không chứa đủ evidence `Ví ShopeePay`, `Thẻ nội địa Napas`, `7 - 14 ngày`, `SPayLater` trong cùng context. Nguyên nhân là bảng thời gian hoàn tiền bị tách thành nhiều chunk, còn embedding ưu tiên các đoạn cùng chủ đề “hoàn tiền” nhưng không đảm bảo đoạn đó có đủ thông tin bảng để trả lời.

Hướng cải thiện là thêm table-aware chunking: giữ bảng nhỏ/vừa thành một chunk, hoặc khi bảng dài thì tách theo nhóm dòng nhưng prepend heading và header bảng vào từng chunk con. Một cách đơn giản khác là tăng `top_k` cho query dạng liệt kê bảng lên 5 để agent có nhiều context hơn.

**Điều hay nhất tôi học được từ benchmark:**  
Kết quả retrieval không nên chỉ nhìn score hoặc đúng `doc_id`; phải kiểm chunk có thật sự chứa bằng chứng trả lời hay không. Metadata filter rất hữu ích khi corpus có tài liệu cùng chủ đề nhưng khác đối tượng, như buyer và seller. Strategy theo heading có thể tái dùng tốt cho policy/FAQ/SOP, nhưng cần bổ sung xử lý bảng nếu domain có nhiều dữ liệu dạng bảng.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |
