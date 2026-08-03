# CP5 Benchmark Draft

Corpus: `data/shopee_selected`

Strategy riêng: `HeadingAwareChunker(chunk_size=700)` trong `bench.py`.

Embedding mặc định khi chạy checkpoint: `mock`. Khi so sánh chất lượng thật ở CP6, nhóm nên chạy cùng một cấu hình `EMBEDDING_PROVIDER=local` nếu máy có model local.

## 5 Benchmark Query Đã Chốt

Không đổi 5 câu này sau khi các thành viên bắt đầu chạy benchmark.

| # | Loại | Query | Metadata filter | Gold answer | Document/chunk kỳ vọng |
|---|---|---|---|---|---|
| 1 | Số liệu | Người mua phải gửi yêu cầu trả hàng hoàn tiền trong bao lâu với thực phẩm tươi sống và với các sản phẩm còn lại? | Không filter | Thực phẩm tươi sống và đông lạnh: trong vòng 24 giờ kể từ lúc đơn hàng cập nhật giao hàng thành công; các sản phẩm còn lại: trong vòng 15 ngày. | `shopee-return-refund-policy`, đoạn 3.2 về thời hạn yêu cầu trả hàng/hoàn tiền; có thể cũng nằm trong `shopee-mall-return-refund-terms`, đoạn 1.9.1. |
| 2 | Điều kiện | Lý do đổi ý khi sản phẩm còn nguyên tem nhãn mác bao bì áp dụng cho nhóm người mua nào và ngoại trừ những loại nào? | `{"customer_role": "buyer"}` | Áp dụng từ 24/11/2025 cho người mua hạng Kim Cương, Vàng và người dùng đăng ký thành công Shopee VIP; ngoại trừ sản phẩm thuộc danh sách hạn chế trả hàng, sản phẩm mua tại Shopee Mart và một số sản phẩm riêng biệt theo quyết định của Shopee. | `shopee-general-return-refund-rules`, bảng điều kiện Trả hàng/Hoàn tiền, dòng `Đổi ý`. |
| 3 | Quy trình + filter bắt buộc | Khi hệ thống ghi nhận đã trả hàng thành công nhưng Shop chưa nhận được hàng hoặc hàng hoàn gặp vấn đề thì phải phản hồi khi nào và hạn phản hồi là bao lâu? | `{"customer_role": "seller"}` | Shop phản hồi từ ngày hệ thống cập nhật trả hàng thành công; hạn phản hồi là trong vòng 2 ngày. | `shopee-seller-manage-return-refund`, mục C, bảng hướng dẫn phản hồi khi chưa nhận được hàng hoàn hoặc hàng hoàn gặp vấn đề. |
| 4 | Liệt kê | Thời gian nhận tiền hoàn qua Ví ShopeePay, thẻ nội địa Napas, thẻ tín dụng ghi nợ và SPayLater là bao lâu? | `{"topic_group": "returns_refunds", "customer_role": "buyer"}` | Ví ShopeePay: 24 giờ; thẻ nội địa Napas: 2-5 ngày làm việc; thẻ tín dụng/ghi nợ: 7-14 ngày làm việc; SPayLater: 24 giờ. | `shopee-refund-time-status`, bảng phương thức hoàn tiền và thời gian hoàn tiền. |
| 5 | Ngoại lệ/troubleshooting | Nếu thanh toán báo lỗi M10 vượt hạn mức thanh toán trong ngày thì Shopee hướng dẫn xử lý thế nào? | `{"topic_group": "payments", "customer_role": "buyer"}` | Với lỗi M10, người mua nên đặt hàng lại vào ngày mai. | `shopee-order-payment-errors`, bảng lỗi thanh toán, dòng `Lỗi (M10)`. |

## Vì Sao 5 Query Này Tốt

- Có đủ dạng: số liệu, điều kiện, quy trình, liệt kê, ngoại lệ.
- Q3 bắt buộc chứng minh metadata filter `customer_role=seller`; nếu không filter, query dễ lẫn với tài liệu buyer về trả hàng/hoàn tiền.
- Q2 và Q4 kiểm tra khả năng giữ bảng trong chunk.
- Q1 kiểm tra khả năng truy xuất đoạn chính sách dài có mốc thời gian.
- Q5 kiểm tra truy xuất một dòng lỗi cụ thể trong bảng troubleshooting.

## Baseline Chunk Comparison

Chạy `ChunkingStrategyComparator().compare()` trên phần body của 3 tài liệu đầu, đã bỏ front matter qua `load_documents()`.

| Document | Fixed size | By sentences | Recursive |
|---|---:|---:|---:|
| `shopee-general-return-refund-rules` | count=17, avg_len=397.9 | count=8, avg_len=764.0 | count=23, avg_len=264.8 |
| `shopee-mall-return-refund-terms` | count=94, avg_len=398.2 | count=56, avg_len=600.0 | count=139, avg_len=241.0 |
| `shopee-order-payment-errors` | count=10, avg_len=395.5 | count=7, avg_len=512.6 | count=14, avg_len=255.7 |

## Checkpoint Command

```bash
python bench.py
```

Kết quả hiện tại:

- Strategy: `HeadingAwareChunker(chunk_size=700)`
- Data dir: `data/shopee_selected`
- Chunks loaded: `392`
- In đủ top-3 và agent answer cho cả 5 query.

Lưu ý: output với `mock` không dùng để kết luận chất lượng semantic. CP5 chỉ cần benchmark chạy được; CP6 mới phân tích tốt/xấu và nên dùng cùng embedder thật giữa các thành viên.
