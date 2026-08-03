# Draft Log: Shopee Selected Corpus

## Mục đích

Tạo corpus chính thức 10 tài liệu từ `data/shopee_cleaned` để đúng checklist lab 5-10 file, nhưng vẫn giữ độ khó đủ cao cho benchmark chunking/retrieval.

Thư mục dùng cho benchmark: `data/shopee_selected`

## Tiêu chí chọn

- Ưu tiên tài liệu có điều kiện, ngoại lệ, thời hạn, quy trình hoặc bảng.
- Giữ đủ các nhóm chủ đề chính: trả hàng/hoàn tiền, logistics hoàn trả, thanh toán, điều khoản dịch vụ.
- Có ít nhất hai giá trị `customer_role`: `buyer`, `seller`, `both`.
- Loại bớt các bài quá hẹp hoặc trùng ý, ví dụ lỗi thẻ riêng lẻ, trả góp riêng lẻ, tracking ngắn.

## Data Inventory Draft

| # | File | Vai trò | Chủ đề | Lý do chọn | Ký tự approx |
|---|---|---|---|---|---:|
| 1 | `shopee-return-refund-policy.md` | both | returns_refunds | Chính sách lõi, nhiều điều kiện và nghĩa vụ của nhiều bên | 19629 |
| 2 | `shopee-general-return-refund-rules.md` | buyer | returns_refunds | Quy định chung, mốc thời gian, lý do khiếu nại, bảng voucher/Xu | 6195 |
| 3 | `shopee-mall-return-refund-terms.md` | both | returns_refunds | Điều khoản Shopee Mall dài, có bảng điều kiện và phí | 34026 |
| 4 | `shopee-review-return-refund-request.md` | buyer | returns_refunds | Quy trình xử lý yêu cầu, failure case, bảng tình trạng hàng hoàn | 8185 |
| 5 | `shopee-seller-manage-return-refund.md` | seller | returns_refunds | File seller duy nhất, dùng tốt cho metadata filter | 3842 |
| 6 | `shopee-return-shipping-methods-fees.md` | buyer | returns_refunds | Phương thức gửi hàng hoàn trả và phí hoàn trả | 5873 |
| 7 | `shopee-refund-time-status.md` | buyer | returns_refunds | Bảng thời gian hoàn tiền theo phương thức thanh toán | 3805 |
| 8 | `shopee-supported-payment-methods.md` | buyer | payments | Bao phủ các phương thức thanh toán, điều kiện áp dụng | 5938 |
| 9 | `shopee-order-payment-errors.md` | buyer | payments | Bảng lỗi thanh toán, phù hợp query dạng troubleshooting | 3623 |
| 10 | `shopee-terms-of-service.md` | both | terms | Điều khoản dài, tốt để stress-test recursive/heading chunking | 83393 |

## Metadata Schema Draft

| Field | Ý nghĩa | Ví dụ |
|---|---|---|
| `doc_id` | ID ổn định, trùng tên file | `shopee-refund-time-status` |
| `title` | Tên tài liệu | `Thời gian nhận tiền hoàn và cách kiểm tra tiền hoàn` |
| `source_url` | URL nguồn công khai | `https://help.shopee.vn/portal/4/article/189473` |
| `retrieved_at` | Ngày lấy dữ liệu | `2026-08-03` |
| `document_version` | Phiên bản/ngày hiệu lực nếu có | `not-stated` |
| `customer_role` | Đối tượng chính | `buyer`, `seller`, `both` |
| `category` | Nhóm nhỏ theo nội dung gốc | `returns-policy`, `payment-policy` |
| `language` | Ngôn ngữ | `vi` |
| `platform` | Nền tảng nguồn | `shopee` |
| `topic_group` | Nhóm chủ đề để filter/A-B test | `returns_refunds`, `payments`, `terms` |
| `policy_type` | Kiểu tài liệu | `legal_policy`, `help_article`, `payment_help`, `seller_guide` |
| `actor_focus` | Vai trò trọng tâm cho query | `buyer`, `seller`, `buyer_seller` |

## Checkpoint Result

- Markdown files: 10
- `sources.csv` rows: 10
- `sources.csv` doc IDs match Markdown `doc_id`: yes
- `file_path` exists: yes
- Required metadata: OK for all 10 files
- Noise scan: no article rating footer/header noise found in selected data files

Distribution:

- `customer_role`: `buyer=6`, `both=3`, `seller=1`
- `topic_group`: `returns_refunds=7`, `payments=2`, `terms=1`
- `policy_type`: `legal_policy=3`, `help_article=4`, `payment_help=2`, `seller_guide=1`

## Gợi ý benchmark tiếp theo

1. Hỏi về thời hạn gửi yêu cầu trả hàng/hoàn tiền cho thực phẩm tươi sống, đơn người bán tự vận chuyển và đơn thông thường.
2. Hỏi về điều kiện hoàn tiền/trả hàng của Shopee Mall.
3. Hỏi seller cần phản hồi trong bao lâu khi hệ thống ghi nhận hàng hoàn thành công nhưng Shop chưa nhận được hàng.
4. Hỏi thời gian hoàn tiền theo từng phương thức thanh toán.
5. Hỏi lỗi thanh toán cụ thể và cách xử lý.

Lưu ý: vì chỉ có 1 file `seller`, query dùng `metadata_filter={"customer_role": "seller"}` nên tập trung vào `shopee-seller-manage-return-refund.md`.
