# CP6 Benchmark Analysis Draft

Corpus: `data/shopee_selected`

Strategy evaluated: `HeadingAwareChunker(chunk_size=700)`

Backend:

- Embedding: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Vector store: Chroma persistent
- Chroma dir: `.chroma/shopee_heading_700`
- Chunks loaded: `392`

Run command:

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

## Summary

| Metric | Result | Meaning |
|---|---:|---|
| `doc hit@3` | `5/5` | Top-3 luôn có đúng tài liệu kỳ vọng. |
| `evidence hit@3` | `4/5` | 4/5 query có chunk chứa chuỗi bằng chứng cần thiết. |
| `chunk-level score` | `6/10` | Theo rubric chunk-level: 2 điểm nếu evidence ở rank 1, 1 điểm nếu evidence ở top-3 nhưng không rank 1, 0 nếu không có evidence. |

Điểm đáng chú ý: nếu chỉ nhìn `doc_id`, strategy có vẻ đạt tuyệt đối `5/5`. Nhưng khi chấm theo chunk chứa đáp án, Q4 fail và Q2/Q5 chỉ đạt 1 điểm vì chunk chứa evidence không đứng rank 1.

## Per-query Result

| Query | Filter | Expected doc rank | Evidence rank | Score | Nhận xét |
|---|---|---:|---:|---:|---|
| Q1 - thời hạn yêu cầu trả hàng | None | 1 | 1 | 2/2 | Tốt. Chunk rank 1 chứa cả mốc 15 ngày và 24 giờ. |
| Q2 - điều kiện đổi ý | `customer_role=buyer` | 1 | 2 | 1/2 | Đúng tài liệu, nhưng chunk rank 1 nói về điều kiện khác; chunk rank 2 mới chứa dòng `Đổi ý` và ngoại lệ Shopee Mart. |
| Q3 - seller phản hồi hàng hoàn | `customer_role=seller` | 1 | 1 | 2/2 | Tốt nhất. Filter đưa đúng seller chunk lên rank 1. |
| Q4 - thời gian hoàn tiền theo phương thức | `topic_group=returns_refunds`, `customer_role=buyer` | 1 | None | 0/2 | Failure chính. Top-3 đều đúng doc nhưng không lấy đúng bảng chứa Napas, thẻ tín dụng/ghi nợ, SPayLater. |
| Q5 - lỗi thanh toán M10 | `category=payment-troubleshooting` | 1 | 2 | 1/2 | Filter hẹp sửa được lỗi lẫn sang payment-methods, nhưng chunk title đứng rank 1; chunk chứa M10 đứng rank 2. |

## A/B Metadata Filter

Query dùng để A/B: Q3.

Question: Khi hệ thống ghi nhận đã trả hàng thành công nhưng Shop chưa nhận được hàng hoặc hàng hoàn gặp vấn đề thì phải phản hồi khi nào và hạn phản hồi là bao lâu?

With filter:

- Filter: `{"customer_role": "seller"}`
- Evidence rank: 1
- Top result: `shopee-seller-manage-return-refund`, chunk 6
- Kết quả: chunk chứa đúng bảng seller, gồm trường hợp Shop chưa nhận được hàng/hàng hoàn gặp vấn đề, thời điểm phản hồi và hạn trong vòng 2 ngày.

Without filter:

- Evidence rank: 3
- Top result bị kéo sang `shopee-return-refund-policy`, chunk 23
- Kết quả: vẫn có thông tin liên quan về người bán phản hồi trong 02 ngày, nhưng hai slot đầu bị nhiễu bởi tài liệu không phải hướng dẫn thao tác seller. Filter làm tăng precision và đẩy chunk đúng từ rank 3 lên rank 1.

Kết luận metadata: filter hữu ích rõ ở Q3. Đánh đổi là recall giảm nếu metadata sai hoặc nếu câu hỏi cần thông tin nằm trong tài liệu `both` nhưng lại filter quá hẹp sang `buyer`/`seller`.

## Failure Case

Failure case chính: Q4.

Query: Thời gian nhận tiền hoàn qua Ví ShopeePay, thẻ nội địa Napas, thẻ tín dụng ghi nợ và SPayLater là bao lâu?

Gold answer: Ví ShopeePay 24 giờ; thẻ nội địa Napas 2-5 ngày làm việc; thẻ tín dụng/ghi nợ 7-14 ngày làm việc; SPayLater 24 giờ.

Evidence expected: `Ví ShopeePay`, `Thẻ nội địa Napas`, `7 - 14 ngày`, `SPayLater`.

Observed top-3:

- Rank 1: `shopee-refund-time-status`, chunk 7, phần lưu ý về ví ShopeePay.
- Rank 2: `shopee-refund-time-status`, chunk 8, phần lưu ý về SPayLater kết hợp phương thức khác.
- Rank 3: `shopee-refund-time-status`, chunk 0, title.

Why this is a real failure:

- `doc_id` đúng nhưng top-3 không chứa chunk bảng chính có đủ Napas, thẻ tín dụng/ghi nợ và SPayLater.
- Embedding xếp các chunk cùng chủ đề "hoàn tiền" cao, nhưng không biết chunk nào có mật độ thông tin bảng cần trả lời.
- Heading-aware chunker giữ heading tốt, nhưng bảng dài bị tách thành nhiều mảnh; chunk chứa bảng đầy đủ chỉ có một cơ hội vào top-k.

Proposed fix:

- Thêm table-aware chunking: giữ nguyên bảng nhỏ/vừa như một chunk, hoặc prepend heading vào từng row-group khi bảng quá dài.
- Tăng `top_k` cho query dạng liệt kê bảng, ví dụ `top_k=5`, rồi để agent tổng hợp.
- Thêm metadata phụ `category=refund-policy` cho Q4 nếu muốn giảm nhiễu trong nhóm returns/refunds.

## Personal Reflection

`HeadingAwareChunker(chunk_size=700)` phù hợp với tài liệu chính sách Shopee vì corpus có nhiều heading, điều khoản và bảng. Strategy này giữ được provenance tốt: top result thường có `doc_id` đúng và chunk còn tiêu đề để debug.

Điểm yếu là bảng dài: heading chunking không tự hiểu rằng nhiều dòng bảng tạo thành một đơn vị trả lời. Vì vậy, strategy này tái dùng tốt cho domain có tài liệu phân mục rõ ràng như policy, FAQ, SOP; nhưng khi đổi sang domain nhiều bảng số liệu, cần thêm table-aware split hoặc tăng top-k.

Filter metadata có giá trị nhất khi cùng chủ đề nhưng khác vai trò người dùng. Q3 chứng minh điều này: không filter vẫn có evidence nhưng ở rank 3; filter `customer_role=seller` đưa đúng chunk lên rank 1. Tuy nhiên filter quá hẹp có thể loại nhầm đáp án, nên chỉ dùng khi query thật sự gắn với vai trò/chủ đề rõ.
