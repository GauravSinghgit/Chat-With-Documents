"""
FAISS vector store with reliable delete support.
Vectors are stored in the pickle metadata alongside text/metadatas,
so we can rebuild the index when deleting — no faiss internals needed.
"""
import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Any
from app.config import settings
from app.utils.logger import logger


class VectorStoreService:
    def __init__(self):
        self.index_path = os.path.join(settings.VECTOR_STORE_PATH, "faiss.index")
        self.metadata_path = os.path.join(settings.VECTOR_STORE_PATH, "metadata.pkl")
        self.dimension = 384

        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
            # Back-compat: old pickles may not have "vectors" key
            if "vectors" not in self.metadata:
                self.metadata["vectors"] = []
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
        else:
            self._init_fresh()

    def _init_fresh(self):
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = {"texts": [], "metadatas": [], "vectors": []}
        logger.info("Initialized fresh FAISS index")

    # ─── Write ────────────────────────────────────────────────────────────────

    def add_documents(
        self,
        texts: List[str],
        embeddings: np.ndarray,
        metadatas: List[Dict[str, Any]],
    ):
        vectors_f32 = embeddings.astype("float32")
        self.index.add(vectors_f32)
        self.metadata["texts"].extend(texts)
        self.metadata["metadatas"].extend(metadatas)
        # Store raw vectors for deletion rebuild
        self.metadata["vectors"].extend(vectors_f32.tolist())
        self._save()
        logger.debug(f"Added {len(texts)} chunks → total vectors: {self.index.ntotal}")

    def delete_by_doc_id(self, doc_id: int):
        """
        Rebuild the FAISS index excluding all chunks of doc_id.
        Works by storing vectors in our own pickle — no FAISS internals needed.
        """
        metas = self.metadata["metadatas"]
        texts = self.metadata["texts"]
        vectors = self.metadata["vectors"]

        keep = [i for i, m in enumerate(metas) if m.get("doc_id") != doc_id]

        if len(keep) == len(metas):
            logger.debug(f"No vectors found for doc_id={doc_id}")
            return

        kept_texts = [texts[i] for i in keep]
        kept_metas = [metas[i] for i in keep]
        kept_vecs = [vectors[i] for i in keep]

        new_index = faiss.IndexFlatIP(self.dimension)
        if kept_vecs:
            arr = np.array(kept_vecs, dtype="float32")
            new_index.add(arr)

        self.index = new_index
        self.metadata = {"texts": kept_texts, "metadatas": kept_metas, "vectors": kept_vecs}
        self._save()
        removed = len(metas) - len(keep)
        logger.info(f"Deleted {removed} vectors for doc_id={doc_id}. Remaining: {new_index.ntotal}")

    # ─── Read ─────────────────────────────────────────────────────────────────

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        if self.index.ntotal == 0:
            return []

        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1).astype("float32"), k
        )

        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.metadata["texts"]):
                results.append({
                    "content": self.metadata["texts"][idx],
                    "metadata": self.metadata["metadatas"][idx],
                    "score": float(distances[0][i]),
                })
        return results

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": "IndexFlatIP (cosine similarity)",
        }

    # ─── Persist ─────────────────────────────────────────────────────────────

    def _save(self):
        os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)
