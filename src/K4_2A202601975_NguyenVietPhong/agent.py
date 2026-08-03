from __future__ import annotations

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

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        if metadata_filter:
            results = self.store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = self.store.search(question, top_k=top_k)

        if not results:
            return self.llm_fn(
                "Instruction: Answer the question.\n\nContext: None\n\nQuestion: "
                f"{question}\n\nAnswer:"
            )

        context_blocks = []
        for idx, item in enumerate(results, start=1):
            doc_id = item.get("metadata", {}).get("doc_id", item.get("id", "unknown"))
            content = item.get("content", "").strip()
            context_blocks.append(f"[{idx}] (doc_id: {doc_id}) {content}")

        context_text = "\n\n".join(context_blocks)

        prompt = (
            "Instruction: Use only the provided context below to answer the question. "
            "If the context is insufficient, state that clearly.\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        return self.llm_fn(prompt)
