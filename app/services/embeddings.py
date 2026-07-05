from sentence_transformers import SentenceTransformer
from app.config import settings
from typing import List
import numpy as np


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

    def embed_query(self, text: str) -> np.ndarray:
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True   # 
        )
        return embedding.astype("float32")

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True   # 
        )
        return embeddings.astype("float32")
