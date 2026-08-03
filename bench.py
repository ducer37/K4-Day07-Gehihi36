"""
bench.py — Benchmark cá nhân của Dũng — Lab 7

Chiến lược: RecursiveChunker(chunk_size=400)
Lý do: Tài liệu chính sách TMĐT có cấu trúc đoạn rõ ràng (## Section, \n\n paragraph).
RecursiveChunker tận dụng được cấu trúc đó tốt hơn FixedSize.

Chạy:
    python bench.py
    EMBEDDING_PROVIDER=local python bench.py   # dùng local embedder để so sánh có ý nghĩa
"""

from __future__ import annotations

import os
import textwrap

from dotenv import load_dotenv

from ingest import build_knowledge_base, load_documents, parse_front_matter
from src.agent import KnowledgeBaseAgent
from src.chunking import ChunkingStrategyComparator, RecursiveChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    LocalEmbedder,
    _mock_embed,
)

# ── CONFIG ────────────────────────────────────────────────────────────────────
DATA_DIR = "data/shopee_cleaned"

# ĐÂY LÀ DÒNG DUY NHẤT KHÁC VỚI CÁC THÀNH VIÊN KHÁC TRONG NHÓM
MY_CHUNKER = RecursiveChunker(chunk_size=400)
MY_STRATEGY_NAME = "RecursiveChunker(chunk_size=400)"

# 5 Benchmark queries (chốt cùng nhóm — không đổi sau khi đã chạy)
# "must_contain": chuỗi đặc trưng PHẢI xuất hiện trong context retrieve được
# → Chấm ở mức CHUNK, không chỉ doc_id (theo rubric Task 7)
BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "type": "số liệu / thời hạn",
        "query": "Thời hạn tối đa để gửi yêu cầu trả hàng hoàn tiền là bao nhiêu ngày?",
        "gold": "15 ngày kể từ lúc đơn hàng cập nhật 'Giao hàng thành công'. "
                "Riêng thực phẩm tươi sống/đông lạnh: 24 giờ.",
        "must_contain": "15 ngày",          # chuỗi đặc trưng trong chunk đáp án
        "expected_doc": "shopee-general-return-refund-rules",
        "filter": None,
    },
    {
        "id": "Q2",
        "type": "điều kiện",
        "query": "Điều kiện để được Trả hàng COM (đổi ý, hàng nguyên vẹn) là gì?",
        "gold": "Chỉ áp dụng cho thành viên hạng Kim Cương, Vàng và người dùng "
                "đăng ký gói Shopee VIP từ ngày 24/11/2025.",
        "must_contain": "Kim Cương",
        "expected_doc": "shopee-return-refund-policy",
        "filter": None,
    },
    {
        "id": "Q3",
        "type": "quy trình",
        "query": "Người bán cần làm gì khi nhận được hàng hoàn trả từ đơn vị vận chuyển?",
        "gold": "Vào Kênh Quản Lý Shop → Trả hàng/Hoàn tiền → Trả hàng thành công "
                "→ Xác nhận Nhận hàng → chọn Nhập lại hàng vào kho (nếu nguyên vẹn) "
                "hoặc Thêm chi phí (nếu thất lạc/hư hỏng).",
        "must_contain": "Xác nhận Nhận hàng",
        "expected_doc": "shopee-seller-manage-return-refund",
        "filter": {"customer_role": "seller"},   # ← A/B test: chạy cả có và không filter
    },
    {
        "id": "Q4",
        "type": "liệt kê",
        "query": "Những lý do nào được chấp nhận để gửi yêu cầu trả hàng hoàn tiền?",
        "gold": "Chưa nhận được hàng, Thiếu hàng, Người bán gửi sai hàng, Hàng bể vỡ "
                "(nhiều loại), Hàng lỗi không hoạt động, Khác với mô tả, Hàng đã qua sử dụng, "
                "Hàng giả/nhái, Đổi ý (với điều kiện hạng thành viên).",
        "must_contain": "Thiếu hàng",
        "expected_doc": "shopee-general-return-refund-rules",
        "filter": None,
    },
    {
        "id": "Q5",
        "type": "ngoại lệ",
        "query": "Trường hợp nào Người bán KHÔNG phải chịu phí vận chuyển chiều hoàn trả?",
        "gold": "Đơn hoàn tiền một phần; lý do 'Chưa nhận được hàng'; do lỗi ĐVVC; "
                "hoàn tiền ngay không cần trả hàng; kênh Người bán tự vận chuyển; "
                "Người mua chọn hình thức 'Tự sắp xếp'.",
        "must_contain": "Người Bán sẽ không phải chịu",
        "expected_doc": "shopee-return-refund-policy",
        "filter": None,
    },
]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def _select_embedder():
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(
                model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL)
            )
        except Exception as e:
            print(f"  [!] Local embedder không sẵn sàng ({e}), dùng mock.")
    return _mock_embed


def _preview(text: str, width: int = 110) -> str:
    return text.replace("\n", " ")[:width] + ("..." if len(text) > width else "")


def _sep(char: str = "─", n: int = 72) -> str:
    return char * n


def _score_query(results: list[dict], q: dict) -> tuple[int, bool, bool]:
    """
    Chấm điểm theo rubric Task 7 — ở mức CHUNK, không chỉ doc_id.

    Returns: (score 0/1/2, doc_relevant_top3, content_relevant_top3)
    - doc_relevant_top3  : doc_id gold có xuất hiện trong top-3?
    - content_relevant_top3: chuỗi must_contain có xuất hiện trong top-3 content?
    """
    must = q.get("must_contain", "")
    expected = q["expected_doc"]

    doc_hit   = any(r["metadata"].get("doc_id") == expected for r in results)
    content_hit = any(must.lower() in r["content"].lower() for r in results) if must else doc_hit

    # Rubric: 2 = content trong top-3, 1 = doc đúng nhưng chunk sai, 0 = không có bằng chứng
    if content_hit:
        score = 2
    elif doc_hit:
        score = 1
    else:
        score = 0

    return score, doc_hit, content_hit


# ── BASELINE ──────────────────────────────────────────────────────────────────
def run_baseline(sample_docs_count: int = 3) -> None:
    print(_sep("═"))
    print("BƯỚC 1: BASELINE — ChunkingStrategyComparator trên 3 tài liệu")
    print(_sep("═"))
    docs = load_documents(DATA_DIR)[:sample_docs_count]
    for doc in docs:
        text = doc.content
        print(f"\nTài liệu: {doc.id}  ({len(text)} ký tự)")
        result = ChunkingStrategyComparator().compare(text, chunk_size=400)
        print(f"  {'Strategy':<20} {'# chunks':>8} {'avg_len':>10}")
        print(f"  {'-'*42}")
        for name, stats in result.items():
            print(f"  {name:<20} {stats['count']:>8} {stats['avg_length']:>10.1f}")


# ── MAIN BENCHMARK ────────────────────────────────────────────────────────────
def run_benchmark(store) -> list[dict]:
    agent = KnowledgeBaseAgent(
        store=store,
        llm_fn=lambda prompt: f"[DEMO LLM]\n{prompt[:300]}..."
    )

    print(_sep("═"))
    print(f"BƯỚC 3: BENCHMARK — 5 queries | {MY_STRATEGY_NAME}")
    print(_sep("═"))

    summary_rows = []

    for q in BENCHMARK_QUERIES:
        print(f"\n{_sep()}")
        print(f"[{q['id']}] Loại: {q['type']}")
        print(f"Query       : {q['query']}")
        print(f"Gold        : {textwrap.fill(q['gold'], 68, initial_indent='              ', subsequent_indent='              ').strip()}")
        print(f"Must contain: \"{q.get('must_contain','')}\"")

        # ── Search bình thường ──
        results = store.search(q["query"], top_k=3)
        score, doc_hit, content_hit = _score_query(results, q)

        print(f"\n  [A] Search KHÔNG filter:")
        for i, r in enumerate(results, 1):
            doc_id   = r["metadata"].get("doc_id", "?")
            chunk_i  = r["metadata"].get("chunk_index", "?")
            sc       = r["score"]
            doc_mark = "✅" if doc_id == q["expected_doc"] else "❌"
            must     = q.get("must_contain", "")
            cnt_mark = "📌" if must and must.lower() in r["content"].lower() else "  "
            print(f"  {i}. {doc_mark}{cnt_mark} score={sc:.4f}  doc={doc_id}  chunk={chunk_i}")
            print(f"     {_preview(r['content'], 100)}")

        print(f"\n  → doc_id top-3: {'✅' if doc_hit else '❌'}  |  "
              f"content top-3 (must_contain): {'✅' if content_hit else '❌'}  |  "
              f"Điểm rubric: {score}/2")

        ab_note = ""
        # ── A/B: chạy lại có filter nếu query có filter (Q3) ──
        if q["filter"]:
            results_f = store.search_with_filter(q["query"], top_k=3, metadata_filter=q["filter"])
            score_f, doc_hit_f, content_hit_f = _score_query(results_f, q)

            print(f"\n  [B] Search CÓ filter {q['filter']}:")
            for i, r in enumerate(results_f, 1):
                doc_id   = r["metadata"].get("doc_id", "?")
                chunk_i  = r["metadata"].get("chunk_index", "?")
                sc       = r["score"]
                doc_mark = "✅" if doc_id == q["expected_doc"] else "❌"
                must     = q.get("must_contain", "")
                cnt_mark = "📌" if must and must.lower() in r["content"].lower() else "  "
                print(f"  {i}. {doc_mark}{cnt_mark} score={sc:.4f}  doc={doc_id}  chunk={chunk_i}")
                print(f"     {_preview(r['content'], 100)}")

            print(f"\n  → doc_id top-3: {'✅' if doc_hit_f else '❌'}  |  "
                  f"content top-3: {'✅' if content_hit_f else '❌'}  |  "
                  f"Điểm rubric: {score_f}/2")
            ab_note = f"A(no filter)={score}/2  B(filter)={score_f}/2"
            # Dùng điểm của lần có filter cho summary
            score, doc_hit, content_hit = score_f, doc_hit_f, content_hit_f

        summary_rows.append({
            "id": q["id"],
            "type": q["type"],
            "score": score,
            "doc_hit": doc_hit,
            "content_hit": content_hit,
            "ab": ab_note,
        })

    return summary_rows


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
def main() -> None:
    print(_sep("═"))
    print("bench.py — Benchmark cá nhân: Dũng")
    print(f"Strategy : {MY_STRATEGY_NAME}")
    print(f"Data dir : {DATA_DIR}")
    print(_sep("═"))

    run_baseline(sample_docs_count=3)

    embedder = _select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"\n{_sep('═')}")
    print(f"BƯỚC 2: NẠP DỮ LIỆU  |  Embedder: {backend}")
    if backend == "mock embeddings fallback":
        print("  ⚠️  Mock — điểm không phản ánh ngữ nghĩa. Dùng EMBEDDING_PROVIDER=local.")
    print(_sep("═"))

    store = build_knowledge_base(DATA_DIR, embedding_fn=embedder, chunker=MY_CHUNKER)
    total_chunks = store.get_collection_size()
    print(f"  ✅ Đã nạp {total_chunks} chunks")

    summary = run_benchmark(store)

    # ── BẢNG TỔNG KẾT ────────────────────────────────────────────────────────
    print(f"\n{_sep('═')}")
    print("BẢNG TỔNG KẾT (Rubric Task 7)")
    print(f"  Strategy: {MY_STRATEGY_NAME}  |  Embedder: {backend}")
    print(_sep())
    print(f"  {'ID':<4} {'Loại':<22} {'doc∈top3':>8} {'chunk∈top3':>10} {'Điểm':>6}  {'A/B'}")
    print(f"  {'-'*68}")
    total = 0
    for r in summary:
        doc_s  = "✅" if r["doc_hit"] else "❌"
        cnt_s  = "✅" if r["content_hit"] else "❌"
        ab     = r["ab"] or ""
        print(f"  {r['id']:<4} {r['type']:<22} {doc_s:>8} {cnt_s:>10} {r['score']:>5}/2  {ab}")
        total += r["score"]
    print(_sep())
    print(f"  TỔNG: {total}/{len(summary)*2} điểm")
    print(_sep("═"))

    print("\n📋 FAILURE CASE ANALYSIS (bắt buộc theo Task 7):")
    for r in summary:
        if r["score"] < 2:
            q = next(x for x in BENCHMARK_QUERIES if x["id"] == r["id"])
            print(f"\n  [{r['id']}] {q['query']}")
            print(f"  Điểm: {r['score']}/2  |  doc_hit={r['doc_hit']}  content_hit={r['content_hit']}")
            print(f"  Nguyên nhân cần phân tích:")
            if not r["content_hit"] and r["doc_hit"]:
                print("    → Đúng tài liệu nhưng sai section: chunk chứa đáp án không lọt top-3.")
                print("      Cosine đo độ giống chủ đề, không đo mật độ thông tin cụ thể.")
            elif not r["doc_hit"]:
                print("    → Không lấy đúng tài liệu: query quá chung, từ khoá xuất hiện ở nhiều doc.")
            print(f"  must_contain: \"{q.get('must_contain','')}\"")
    print()


if __name__ == "__main__":
    main()
