from __future__ import annotations

import os
import re
import sys

from ingest import build_knowledge_base, load_documents
from src.agent import KnowledgeBaseAgent
from src.chunking import ChunkingStrategyComparator, FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import EMBEDDING_PROVIDER_ENV, LOCAL_EMBEDDING_MODEL, LocalEmbedder, _mock_embed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


DATA_DIR = os.getenv("LAB_DATA_DIR", "data/shopee_selected")
VECTOR_STORE = os.getenv("VECTOR_STORE", "memory").strip().lower()
CHROMA_DIR = os.getenv("CHROMA_DIR", ".chroma")
CHUNKER = os.getenv("CHUNKER", "heading").strip().lower()
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "700"))


BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "type": "số liệu",
        "query": "Người mua phải gửi yêu cầu trả hàng hoàn tiền trong bao lâu với thực phẩm tươi sống và với các sản phẩm còn lại?",
        "filter": None,
        "gold": "Thực phẩm tươi sống và đông lạnh: trong vòng 24 giờ kể từ lúc đơn hàng cập nhật giao hàng thành công; các sản phẩm còn lại: trong vòng 15 ngày.",
        "expected_doc": "shopee-return-refund-policy",
        "evidence": ["trong vòng 15", "trong vòng 24"],
    },
    {
        "id": "Q2",
        "type": "điều kiện",
        "query": "Lý do đổi ý khi sản phẩm còn nguyên tem nhãn mác bao bì áp dụng cho nhóm người mua nào và ngoại trừ những loại nào?",
        "filter": {"customer_role": "buyer"},
        "gold": "Áp dụng từ 24/11/2025 cho người mua hạng Kim Cương, Vàng và người dùng đăng ký thành công Shopee VIP; ngoại trừ sản phẩm thuộc danh sách hạn chế trả hàng, sản phẩm mua tại Shopee Mart và một số sản phẩm riêng biệt theo quyết định của Shopee.",
        "expected_doc": "shopee-general-return-refund-rules",
        "evidence": ["Đổi ý", "Shopee Mart"],
    },
    {
        "id": "Q3",
        "type": "quy trình + filter",
        "query": "Khi hệ thống ghi nhận đã trả hàng thành công nhưng Shop chưa nhận được hàng hoặc hàng hoàn gặp vấn đề thì phải phản hồi khi nào và hạn phản hồi là bao lâu?",
        "filter": {"customer_role": "seller"},
        "gold": "Shop phản hồi từ ngày hệ thống cập nhật trả hàng thành công; hạn phản hồi là trong vòng 2 ngày.",
        "expected_doc": "shopee-seller-manage-return-refund",
        "evidence": ["trả hàng thành công", "Trong vòng2 ngày"],
    },
    {
        "id": "Q4",
        "type": "liệt kê",
        "query": "Thời gian nhận tiền hoàn qua Ví ShopeePay, thẻ nội địa Napas, thẻ tín dụng ghi nợ và SPayLater là bao lâu?",
        "filter": {"topic_group": "returns_refunds", "customer_role": "buyer"},
        "gold": "Ví ShopeePay: 24 giờ; thẻ nội địa Napas: 2-5 ngày làm việc; thẻ tín dụng/ghi nợ: 7-14 ngày làm việc; SPayLater: 24 giờ.",
        "expected_doc": "shopee-refund-time-status",
        "evidence": ["Ví ShopeePay", "Thẻ nội địa Napas", "7 - 14 ngày", "SPayLater"],
    },
    {
        "id": "Q5",
        "type": "ngoại lệ",
        "query": "Nếu thanh toán báo lỗi M10 vượt hạn mức thanh toán trong ngày thì Shopee hướng dẫn xử lý thế nào?",
        "filter": {"category": "payment-troubleshooting"},
        "gold": "Với lỗi M10, người mua nên đặt hàng lại vào ngày mai.",
        "expected_doc": "shopee-order-payment-errors",
        "evidence": ["Lỗi (M10)", "ngày mai"],
    },
]


class HeadingAwareChunker:
    """Split markdown by headings; long sections fall back to RecursiveChunker."""

    def __init__(self, chunk_size: int = 700) -> None:
        self.chunk_size = chunk_size
        self._fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        sections = [section.strip() for section in re.split(r"(?m)(?=^#{1,6}\s+)", text) if section.strip()]
        chunks: list[str] = []
        for section in sections:
            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue
            heading = section.splitlines()[0] if section.startswith("#") else ""
            for index, piece in enumerate(self._fallback.chunk(section)):
                chunks.append(piece if index == 0 or not heading else f"{heading}\n{piece}")
        return chunks


def demo_llm(prompt: str) -> str:
    preview = prompt[:500].replace("\n", " ")
    return f"[DEMO LLM] {preview}..."


def select_embedder():
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
    return _mock_embed


def print_baseline(data_dir: str) -> None:
    print("=== Baseline chunk comparison: 3 documents, body only ===")
    comparator = ChunkingStrategyComparator()
    for doc in load_documents(data_dir)[:3]:
        stats = comparator.compare(doc.content, chunk_size=400)
        row = ", ".join(
            f"{name}: count={item['count']}, avg_len={item['avg_length']:.1f}"
            for name, item in stats.items()
        )
        print(f"- {doc.id}: {row}")


def select_chunker():
    if CHUNKER == "fixed":
        return FixedSizeChunker(chunk_size=CHUNK_SIZE, overlap=max(0, CHUNK_SIZE // 10))
    if CHUNKER == "recursive":
        return RecursiveChunker(chunk_size=CHUNK_SIZE)
    if CHUNKER == "sentence":
        return SentenceChunker()
    return HeadingAwareChunker(chunk_size=CHUNK_SIZE)


def evidence_rank(results: list[dict], needles: list[str]) -> int | None:
    for index, result in enumerate(results, start=1):
        content = result["content"].lower()
        if all(needle.lower() in content for needle in needles):
            return index
    return None


def print_results(results: list[dict]) -> None:
    for index, result in enumerate(results, start=1):
        metadata = result["metadata"]
        preview = result["content"][:180].replace("\n", " ")
        print(
            f"{index}. score={result['score']:.3f} "
            f"doc_id={metadata.get('doc_id')} chunk={metadata.get('chunk_index')} "
            f"preview={preview}..."
        )


def main() -> int:
    chunker = select_chunker()
    embedding_fn = select_embedder()
    use_chroma = VECTOR_STORE == "chroma"
    collection_name = os.getenv("CHROMA_COLLECTION", f"lab7_shopee_{CHUNKER}_{CHUNK_SIZE}")
    store = build_knowledge_base(
        DATA_DIR,
        embedding_fn,
        chunker=chunker,
        collection_name=collection_name,
        use_chroma=use_chroma,
        persist_dir=CHROMA_DIR,
        reset_collection=use_chroma,
    )
    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)

    print(f"Strategy: {chunker.__class__.__name__}(chunk_size={getattr(chunker, 'chunk_size', 'n/a')})")
    print(f"Data dir: {DATA_DIR}")
    print(f"Embedding: {getattr(embedding_fn, '_backend_name', embedding_fn.__class__.__name__)}")
    print(f"Vector store: {'chroma' if use_chroma else 'memory'}")
    if use_chroma:
        print(f"Chroma dir: {CHROMA_DIR}")
        print(f"Chroma collection: {collection_name}")
    print(f"Chunks loaded: {store.get_collection_size()}")
    print()
    print_baseline(DATA_DIR)

    doc_hits = 0
    evidence_hits = 0
    score_total = 0
    for case in BENCHMARK_QUERIES:
        print()
        print(f"=== {case['id']} [{case['type']}] ===")
        print(f"Query: {case['query']}")
        print(f"Filter: {case['filter']}")
        print(f"Gold: {case['gold']}")
        print(f"Expected doc: {case['expected_doc']}")

        results = store.search_with_filter(case["query"], top_k=3, metadata_filter=case["filter"])
        rank = next(
            (index for index, result in enumerate(results, start=1) if result["metadata"].get("doc_id") == case["expected_doc"]),
            None,
        )
        evidence_at = evidence_rank(results, case["evidence"])
        case_score = 2 if evidence_at == 1 else 1 if evidence_at else 0
        doc_hits += int(rank is not None)
        evidence_hits += int(evidence_at is not None)
        score_total += case_score
        print(f"Expected doc in top-3: {'yes, rank ' + str(rank) if rank else 'no'}")
        print(f"Evidence in top-3: {'yes, rank ' + str(evidence_at) if evidence_at else 'no'}")
        print(f"Chunk-level score: {case_score}/2")
        print("Top-3:")
        print_results(results)
        if case["id"] == "Q3":
            ab_results = store.search(case["query"], top_k=3)
            ab_evidence_at = evidence_rank(ab_results, case["evidence"])
            print("A/B without metadata_filter:")
            print(f"Evidence without filter: {'yes, rank ' + str(ab_evidence_at) if ab_evidence_at else 'no'}")
            print_results(ab_results)
        print("Agent answer:")
        print(agent.answer(case["query"], top_k=3, metadata_filter=case["filter"]))

    print()
    print(f"Doc hit@3: {doc_hits}/{len(BENCHMARK_QUERIES)}")
    print(f"Evidence hit@3: {evidence_hits}/{len(BENCHMARK_QUERIES)}")
    print(f"Chunk-level score: {score_total}/{len(BENCHMARK_QUERIES) * 2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
