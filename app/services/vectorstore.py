import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Any
from app.config import settings

class VectorStoreService:
    def __init__(self):
        self.index_path = os.path.join(settings.VECTOR_STORE_PATH, "faiss.index")
        self.metadata_path = os.path.join(settings.VECTOR_STORE_PATH, "metadata.pkl")
        self.dimension = 384
        
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            self.index = faiss.IndexFlatIP(self.dimension)

            self.metadata = {"texts": [], "metadatas": []}
    
    def add_documents(self, texts: List[str], embeddings: np.ndarray, metadatas: List[Dict[str, Any]]):
        self.index.add(embeddings.astype("float32"))
        self.metadata["texts"].extend(texts)
        self.metadata["metadatas"].extend(metadatas)
        self._save()
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        if self.index.ntotal == 0:
            return []
        
        distances, indices = self.index.search(query_embedding.reshape(1, -1).astype("float32"), k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata["texts"]):
                results.append({
                    "content": self.metadata["texts"][idx],
                    "metadata": self.metadata["metadatas"][idx],
                    "score": float(distances[0][i])
                })
        return results
    
    def _save(self):
        os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)