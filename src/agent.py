from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3, metadata_filter: dict | None = None) -> str:
        results = self.store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        if not results:
            return "Không có dữ liệu phù hợp trong knowledge base để trả lời."

        context_lines = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("doc_id") or metadata.get("source_url") or metadata.get("source") or result.get("id")
            context_lines.append(f"[{index}] source={source}\n{result['content']}")

        prompt = (
            "Instruction: Chỉ dùng context bên dưới để trả lời. "
            "Nếu context không đủ, hãy nói rõ là không đủ thông tin.\n\n"
            f"Context:\n{'\n\n'.join(context_lines)}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
