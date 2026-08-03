# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Gehihi36  
**Thành viên:**

- Nguyễn Việt Phong — 2A202601975
- Nguyễn Tuấn Đức — 2A202601380
- Lê Trọng Việt Dũng — 2A202601746
- Ngô Quang Anh — 2A202601106

**Ngày:** 03/08/2026

---

## 1. Lựa Chọn Tài Liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm Vi Bộ Tài Liệu

Chủ đề cố định của lớp K4 là chính sách thương mại điện tử và hỗ trợ khách hàng. Nhóm Gehihi36 chọn phạm vi cụ thể là **chính sách Shopee liên quan đến trả hàng, hoàn tiền, thanh toán và điều khoản dịch vụ**, vì đây là nhóm tài liệu có nhiều điều kiện, ngoại lệ, bảng thời gian và phân vai buyer/seller đủ tốt để kiểm thử chunking, metadata filter và retrieval ở mức chunk.

Nhóm giữ dữ liệu theo ba mức để minh bạch quá trình xử lý:

- `data/shopee_full`: dữ liệu crawl/thu thập ban đầu từ các nguồn công khai của Shopee, còn rộng và có thể chứa nhiều nội dung chưa phù hợp để benchmark.
- `data/shopee_cleaned`: dữ liệu đã làm sạch từ bản thu thập ban đầu, loại bớt menu/footer, phần đánh giá bài viết, nội dung lặp và các đoạn nhiễu.
- `data/shopee_selected`: 10 tài liệu tốt nhất được chọn từ dữ liệu đã làm sạch để làm corpus benchmark chính.

Corpus chính dùng cho benchmark nằm tại:

```text
data/shopee_selected
```

Tập này gồm 10 tài liệu markdown đã làm sạch, kèm `sources.csv`. Dữ liệu được lấy từ các trang hỗ trợ/chính sách công khai của Shopee, không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.

### Data Inventory

| # | Tài liệu | Source URL | Ngày lấy / phiên bản | Số ký tự | Metadata chính |
|---|---|---|---:|---:|---|
| 1 | Những quy định chung về trả hàng và hoàn tiền | `https://help.shopee.vn/portal/4/article/188931` | `2026-08-03` / `not-stated` | 6,124 | `customer_role=buyer`, `category=returns-policy`, `topic_group=returns_refunds` |
| 2 | Điều khoản dịch vụ Shopee Mall về trả hàng và hoàn tiền | `https://help.shopee.vn/portal/4/article/77262` | `2026-08-03` / `not-stated` | 33,709 | `customer_role=both`, `category=returns-policy`, `policy_type=legal_policy` |
| 3 | Lý do không thể thanh toán đơn hàng trên Shopee | `https://help.shopee.vn/portal/4/article/84824` | `2026-08-03` / `not-stated` | 3,595 | `customer_role=buyer`, `category=payment-troubleshooting`, `topic_group=payments` |
| 4 | Thời gian nhận tiền hoàn và cách kiểm tra tiền hoàn | `https://help.shopee.vn/portal/4/article/189473` | `2026-08-03` / `not-stated` | 3,767 | `customer_role=buyer`, `category=refund-policy`, `topic_group=returns_refunds` |
| 5 | Chính sách trả hàng và hoàn tiền | `https://help.shopee.vn/portal/4/article/77251?seo=1` | `2026-08-03` / `not-stated` | 19,426 | `customer_role=both`, `category=returns-policy`, `policy_type=legal_policy` |
| 6 | Các phương thức gửi hàng hoàn trả và phí hoàn trả | `https://help.shopee.vn/portal/4/article/189477` | `2026-08-03` / `not-stated` | 5,779 | `customer_role=buyer`, `category=return-logistics`, `topic_group=returns_refunds` |
| 7 | Quy trình Shopee xử lý yêu cầu trả hàng và hoàn tiền | `https://help.shopee.vn/portal/4/article/190242` | `2026-08-03` / `not-stated` | 8,064 | `customer_role=buyer`, `category=return-dispute`, `topic_group=returns_refunds` |
| 8 | Quản lý đơn trả hàng hoàn tiền | `https://help.shopee.vn/portal/1/article/102521` | `2026-08-03` / `not-stated` | 3,734 | `customer_role=seller`, `category=after-sales-process`, `topic_group=returns_refunds` |
| 9 | Các phương thức thanh toán được Shopee hỗ trợ | `https://help.shopee.vn/portal/4/article/79198` | `2026-08-03` / `not-stated` | 5,804 | `customer_role=buyer`, `category=payment-policy`, `topic_group=payments` |
| 10 | Điều khoản dịch vụ Shopee | `https://help.shopee.vn/portal/4/article/77243` | `2026-08-03` / `not-stated` | 82,940 | `customer_role=both`, `category=terms-of-service`, `policy_type=terms` |

### Data Governance Checklist

- [x] Corpus chỉ chứa nguồn công khai/được phép dùng.
- [x] Không đưa dữ liệu cá nhân, thông tin đăng nhập, dữ liệu nội bộ hoặc nội dung cần vượt CAPTCHA/đăng nhập vào repo.
- [x] Mỗi tài liệu có `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`.
- [x] `sources.csv` khớp một-một với 10 file markdown trong `data/shopee_selected`.
- [x] Field phân vai `customer_role` có nhiều hơn một giá trị: `buyer`, `seller`, `both`, nên metadata filter có ý nghĩa thực tế.

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ | Tác dụng với retrieval |
|---|---|---|---|
| `doc_id` | string | `shopee-seller-manage-return-refund` | Truy vết chunk về file gốc, dùng cho `delete_document` và đánh giá doc hit. |
| `title` | string | `Quản lý đơn trả hàng hoàn tiền` | Hiển thị nguồn dễ hiểu khi debug và demo. |
| `source_url` | string | URL trang Help Center Shopee | Minh bạch provenance, giúp kiểm chứng câu trả lời. |
| `retrieved_at` | date string | `2026-08-03` | Biết thời điểm lấy dữ liệu. |
| `document_version` | string | `not-stated` | Ghi nhận phiên bản/ngày hiệu lực nếu nguồn có nêu. |
| `customer_role` | enum | `buyer`, `seller`, `both` | Filter theo vai trò người dùng; quan trọng nhất ở Q3. |
| `category` | string | `payment-troubleshooting` | Filter theo nhóm vấn đề hẹp, ví dụ lỗi thanh toán M10 ở Q5. |
| `topic_group` | enum | `returns_refunds`, `payments`, `terms` | Filter theo chủ đề lớn để giảm nhiễu giữa hoàn tiền, thanh toán và điều khoản. |
| `policy_type` | string | `help_article`, `legal_policy`, `seller_guide` | Phân biệt bài hướng dẫn, điều khoản pháp lý và hướng dẫn seller. |
| `chunk_index` | integer | `6` | Được `ingest.py` gắn vào từng chunk để truy vết đúng đoạn. |

---

## 2. Thiết Kế Chiến Lược (Strategy Design) — Nhóm (15 điểm)

### Baseline Analysis

Nhóm chạy `ChunkingStrategyComparator().compare()` trên phần body của 3 tài liệu, không tính YAML front matter. Mục tiêu baseline là quan sát số chunk và độ dài trung bình trước khi chọn strategy riêng.

| Tài liệu | Fixed size | By sentences | Recursive |
|---|---:|---:|---:|
| `shopee-general-return-refund-rules` | 17 chunks / avg 397.9 | 8 chunks / avg 764.0 | 23 chunks / avg 264.8 |
| `shopee-mall-return-refund-terms` | 94 chunks / avg 398.2 | 56 chunks / avg 600.0 | 139 chunks / avg 241.0 |
| `shopee-order-payment-errors` | 10 chunks / avg 395.5 | 7 chunks / avg 512.6 | 14 chunks / avg 255.7 |

Nhận xét baseline: fixed-size dễ ổn định về kích thước nhưng có thể cắt ngang bảng/điều kiện; sentence chunking giữ câu tự nhiên nhưng tạo chunk dài, dễ loãng với tài liệu chính sách; recursive chunking an toàn hơn về cấu trúc nhưng nhiều chunk nhỏ làm tăng số vector và có thể tách điều kiện khỏi ngoại lệ. Vì corpus Shopee có nhiều heading và bảng, nhóm ưu tiên các strategy giữ cấu trúc mục.

### Chiến Lược Của Từng Thành Viên

**Nguyễn Tuấn Đức — HeadingAwareChunker(chunk_size=700)**

- Loại strategy: custom heading-aware + recursive fallback.
- Mô tả: tách trước mỗi heading markdown; section nào dài hơn 700 ký tự thì fallback sang `RecursiveChunker`; khi tách section dài, prepend lại heading vào chunk con để không mất ngữ cảnh.
- Lý do: phù hợp với chính sách Shopee vì nội dung được biên soạn theo mục như điều kiện, lưu ý, quy trình và thời gian hoàn tiền.

```python
sections = split_before_markdown_heading(text)
for section in sections:
    if len(section) <= 700:
        keep(section)
    else:
        split_by_recursive(section)
        prepend_heading_to_child_chunks()
```

**Nguyễn Việt Phong — RecursiveChunker / section-oriented baseline**

- Loại strategy: recursive chunking dựa trên separator tự nhiên.
- Mô tả: ưu tiên tách theo đoạn, dòng, câu, từ rồi mới cắt cứng khi không còn separator phù hợp.
- Lý do: chiến lược này tái dùng tốt khi tài liệu không có heading markdown sạch hoặc có nhiều đoạn văn bản dài; nó giảm nguy cơ cắt giữa câu so với fixed-size thuần.

**Lê Trọng Việt Dũng — Sentence/semantic chunking**

- Loại strategy: sentence-based / semantic-oriented chunking.
- Mô tả: tách theo ranh giới câu rồi gom nhiều câu thành chunk để giữ đơn vị ngôn ngữ tự nhiên.
- Lý do: phù hợp với các đoạn giải thích ngắn hoặc FAQ dạng văn xuôi, hạn chế việc retrieval trả về chunk bị cắt giữa câu.

**Ngô Quang Anh — Fixed/recursive tuned chunking**

- Loại strategy: fixed-size hoặc recursive tuned baseline.
- Mô tả: dùng chunk size cố định hoặc recursive với tham số đơn giản để tạo đường cơ sở dễ so sánh.
- Lý do: baseline ổn định giúp nhóm thấy rõ lợi ích của strategy theo cấu trúc tài liệu, đặc biệt khi so với heading-aware trên corpus chính sách nhiều mục.

### So Sánh Giữa Các Thành Viên

| Thành viên | Strategy | Điểm truy xuất | Điểm mạnh | Điểm yếu |
|---|---|---:|---|---|
| Nguyễn Tuấn Đức | `HeadingAwareChunker(chunk_size=700)` + local embedding + Chroma | 6/10 chunk-level; doc hit@3 5/5 | Giữ heading, provenance rõ, Q3 filter rất tốt | Chưa table-aware nên fail Q4 dạng bảng |
| Nguyễn Việt Phong | Recursive/section-oriented | Kết quả cá nhân đạt top-3 liên quan tốt trong báo cáo riêng | Tái dùng tốt, ít cắt giữa cấu trúc tự nhiên | Có thể tạo nhiều chunk nhỏ, tăng chi phí embedding |
| Lê Trọng Việt Dũng | Sentence/semantic chunking | Có top-3 liên quan cho 5 query theo báo cáo riêng | Chunk dễ đọc, ít vỡ câu | Với bảng/chính sách dài, chunk có thể thiếu heading hoặc điều kiện |
| Ngô Quang Anh | Fixed/recursive tuned baseline | Dùng làm baseline đối chứng | Đơn giản, dễ kiểm soát kích thước | Dễ cắt ngang bảng hoặc điều kiện/ngoại lệ |

Chiến lược phù hợp nhất với corpus Shopee là **heading-aware chunking** vì tài liệu chính sách có cấu trúc mục rõ ràng. Tuy nhiên, kết quả Q4 cho thấy heading-aware chưa đủ với bảng dài: nếu câu trả lời nằm trong nhiều dòng bảng, retrieval có thể tìm đúng tài liệu nhưng sai chunk. Vì vậy hướng tối ưu tiếp theo là kết hợp heading-aware với table-aware chunking.

---

## 3. Câu Hỏi Đánh Giá & Chất Lượng Truy Xuất (Retrieval Quality) — Nhóm (10 điểm)

### Benchmark Queries Và Gold Answers

Nhóm chốt đúng 5 query cố định, bao phủ số liệu, điều kiện, quy trình, liệt kê và ngoại lệ. Các query này dùng chung cho benchmark cá nhân để so sánh công bằng.

| # | Loại | Query | Gold answer | Document/chunk kỳ vọng |
|---|---|---|---|---|
| 1 | Số liệu | Người mua phải gửi yêu cầu trả hàng hoàn tiền trong bao lâu với thực phẩm tươi sống và với các sản phẩm còn lại? | Thực phẩm tươi sống/đông lạnh: trong vòng 24 giờ; các sản phẩm còn lại: trong vòng 15 ngày. | `shopee-return-refund-policy`, chunk chứa `trong vòng 15` và `trong vòng 24` |
| 2 | Điều kiện | Lý do đổi ý khi sản phẩm còn nguyên tem nhãn mác bao bì áp dụng cho nhóm người mua nào và ngoại trừ những loại nào? | Áp dụng cho hạng Kim Cương, Vàng và Shopee VIP; ngoại trừ danh sách hạn chế, Shopee Mart và một số sản phẩm riêng biệt. | `shopee-general-return-refund-rules`, chunk chứa `Đổi ý` và `Shopee Mart` |
| 3 | Quy trình + filter | Khi hệ thống ghi nhận đã trả hàng thành công nhưng Shop chưa nhận được hàng hoặc hàng hoàn gặp vấn đề thì phải phản hồi khi nào và hạn phản hồi là bao lâu? | Shop phản hồi từ ngày hệ thống cập nhật trả hàng thành công; hạn phản hồi trong vòng 2 ngày. | `shopee-seller-manage-return-refund`, chunk seller table |
| 4 | Liệt kê | Thời gian nhận tiền hoàn qua Ví ShopeePay, thẻ nội địa Napas, thẻ tín dụng/ghi nợ và SPayLater là bao lâu? | ShopeePay: 24 giờ; Napas: 2-5 ngày làm việc; thẻ tín dụng/ghi nợ: 7-14 ngày làm việc; SPayLater: 24 giờ. | `shopee-refund-time-status`, chunk bảng thời gian hoàn tiền |
| 5 | Ngoại lệ | Nếu thanh toán báo lỗi M10 vượt hạn mức thanh toán trong ngày thì Shopee hướng dẫn xử lý thế nào? | Với lỗi M10, người mua nên đặt hàng lại vào ngày mai. | `shopee-order-payment-errors`, chunk chứa `Lỗi (M10)` và `ngày mai` |

### Cấu Hình Benchmark Chính

Benchmark chính của nhóm dùng cấu hình thật cho retrieval:

```powershell
$env:EMBEDDING_PROVIDER='local'
$env:VECTOR_STORE='chroma'
$env:CHROMA_DIR='.chroma\shopee_heading_700'
$env:CHUNKER='heading'
$env:CHUNK_SIZE='700'
conda run -n vmec-clinical-copilot python bench.py
```

- Embedder: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Số chiều embedding: 384
- Vector store: Chroma persistent
- Số chunk nạp vào store: 392
- Agent answer trong benchmark dùng `demo_llm`/mock-style function để deterministic; phần retrieval, embedding và Chroma là thật.

### Tổng Hợp Kết Quả Truy Xuất

| # | Query | Metadata filter | Expected doc rank | Evidence rank | Score | Ghi chú |
|---|---|---|---:|---:|---:|---|
| 1 | Thời hạn yêu cầu trả hàng | None | 1 | 1 | 2/2 | Tốt; top-1 chứa cả mốc 15 ngày và 24 giờ. |
| 2 | Điều kiện đổi ý | `customer_role=buyer` | 1 | 2 | 1/2 | Đúng document; evidence nằm rank 2, top-1 chưa đủ chi tiết. |
| 3 | Seller phản hồi hàng hoàn | `customer_role=seller` | 1 | 1 | 2/2 | Filter đưa đúng seller chunk lên rank 1. |
| 4 | Thời gian hoàn tiền theo phương thức | `topic_group=returns_refunds`, `customer_role=buyer` | 1 | None | 0/2 | Failure chính: đúng document nhưng top-3 thiếu bảng đầy đủ. |
| 5 | Lỗi thanh toán M10 | `category=payment-troubleshooting` | 1 | 2 | 1/2 | Filter đúng nhóm payment; evidence M10 nằm rank 2. |

Tổng kết:

- `Doc hit@3`: 5/5
- `Evidence hit@3`: 4/5
- `Chunk-level score`: 6/10

Điểm quan trọng là nếu chỉ nhìn `doc_id`, kết quả có vẻ hoàn hảo vì 5/5 query đều tìm được đúng tài liệu trong top-3. Nhưng khi chấm đúng ở mức chunk chứa bằng chứng, Q4 fail và Q2/Q5 chỉ đạt 1 điểm vì evidence không đứng rank 1.

### A/B Metadata Filter

Query dùng để chứng minh filter là Q3, vì cùng chủ đề trả hàng/hoàn tiền nhưng buyer và seller có đáp án khác nhau.

- Có filter `{"customer_role": "seller"}`: evidence đứng rank 1, top result là `shopee-seller-manage-return-refund`, chunk 6.
- Không filter: evidence vẫn xuất hiện nhưng rơi xuống rank 3; hai slot đầu bị nhiễu bởi tài liệu không phải hướng dẫn thao tác seller.

Kết luận: metadata filter không thay thế embedding search, mà thu hẹp không gian tìm kiếm trước khi ranking. Filter tăng precision rõ ràng khi query có vai trò cụ thể, nhưng có đánh đổi recall nếu metadata sai hoặc câu hỏi cần thông tin trong tài liệu `both`.

---

## 4. Thuyết Trình (Demo) & Bài Học Nhóm — Nhóm (5 điểm)

### Insight Chính Khi Demo

- Pipeline RAG hoàn chỉnh gồm: load corpus -> parse metadata -> chunk -> embed -> store vào Chroma -> retrieve top-k -> agent answer có context.
- Local embedding + Chroma được dùng cho benchmark thật; mock chỉ dùng cho unit test và `demo_llm` để deterministic.
- Metadata có giá trị rõ nhất ở Q3: filter `customer_role=seller` đưa evidence từ rank 3 lên rank 1.
- Failure Q4 cho thấy đúng document chưa chắc đúng chunk. RAG cần chấm evidence-level, không chỉ doc-level.

### Failure Case

Failure case chính là Q4: top-3 đều thuộc đúng tài liệu `shopee-refund-time-status`, nhưng không có chunk nào chứa đủ bảng thời gian hoàn tiền cho ShopeePay, Napas, thẻ tín dụng/ghi nợ và SPayLater. Nguyên nhân là embedding ưu tiên chunk cùng chủ đề "hoàn tiền", còn heading-aware chunking chưa hiểu bảng dài là một đơn vị trả lời hoàn chỉnh.

Hướng cải thiện:

- Thêm table-aware chunking để giữ bảng nhỏ/vừa nguyên khối.
- Nếu bảng dài, tách theo nhóm dòng nhưng prepend heading và header bảng vào từng chunk con.
- Tăng `top_k` cho query dạng liệt kê bảng, ví dụ từ 3 lên 5.
- Có thể thêm reranker hoặc kiểm evidence string sau retrieval để ưu tiên chunk chứa thông tin trả lời trực tiếp.

### Bài Học Nhóm

Nhóm rút ra rằng chất lượng RAG phụ thuộc mạnh vào dữ liệu và chunking, không chỉ vào model embedding. Với tài liệu chính sách, chunk theo cấu trúc heading tốt hơn chunk cứng vì giữ được điều kiện, ngoại lệ và provenance. Tuy nhiên, với bảng, heading-aware vẫn chưa đủ; cần thêm logic domain-aware cho bảng.

Metadata filter hữu ích khi corpus có tài liệu cùng từ vựng nhưng khác đối tượng, như buyer và seller. Dù vậy filter phải dùng có kiểm soát vì nó tăng precision nhưng có thể giảm recall. Khi đổi domain, strategy heading-aware có thể tái dùng cho policy/FAQ/SOP, nhưng nếu domain là chat log hoặc bảng số liệu thì cần đổi chunker tương ứng.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 7 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **36 / 40** |
