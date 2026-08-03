from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
        use_chroma: bool | None = None,
        persist_dir: str | Path = ".chroma",
        reset_collection: bool = False,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = bool(use_chroma) if use_chroma is not None else os.getenv("VECTOR_STORE") == "chroma"
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._client = None
        self._next_index = 0

        if self._use_chroma:
            try:
                import chromadb
            except Exception as exc:
                raise RuntimeError("ChromaDB is not installed. Install it with: python -m pip install chromadb") from exc

            self._client = chromadb.PersistentClient(path=str(persist_dir))
            if reset_collection:
                try:
                    self._client.delete_collection(collection_name)
                except Exception:
                    pass
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata)
        metadata.setdefault("doc_id", doc.id.split("::", 1)[0])
        return {
            "id": f"{doc.id}::{self._next_index}",
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

    def _make_chroma_result(self, query_result: dict[str, Any]) -> list[dict[str, Any]]:
        ids = query_result.get("ids", [[]])[0]
        documents = query_result.get("documents", [[]])[0]
        metadatas = query_result.get("metadatas", [[]])[0]
        distances = query_result.get("distances", [[]])[0]
        return [
            {
                "id": ids[index],
                "content": documents[index],
                "metadata": metadatas[index] or {},
                "score": 1 - distances[index],
            }
            for index in range(len(ids))
        ]

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_vector = self._embedding_fn(query)
        scored = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": _dot(query_vector, record["embedding"]),
            }
            for record in records
        ]
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        for doc in docs:
            record = self._make_record(doc)
            self._next_index += 1
            if self._use_chroma:
                self._collection.add(
                    ids=[record["id"]],
                    documents=[record["content"]],
                    metadatas=[record["metadata"]],
                    embeddings=[record["embedding"]],
                )
            else:
                self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma:
            if self.get_collection_size() == 0:
                return []
            result = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            return self._make_chroma_result(result)
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if metadata_filter is None:
            return self.search(query, top_k=top_k)
        if self._use_chroma:
            if self.get_collection_size() == 0:
                return []
            result = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=top_k,
                where=metadata_filter,
                include=["documents", "metadatas", "distances"],
            )
            return self._make_chroma_result(result)
        records = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma:
            matches = self._collection.get(where={"doc_id": doc_id})
            ids = matches.get("ids", [])
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True
        before = len(self._store)
        self._store = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]
        return len(self._store) != before
