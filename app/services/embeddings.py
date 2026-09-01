"""Local embedding index. No external terminology API is used."""
from pathlib import Path


class EmbeddingIndex:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.codes: list[str] = []

    def _load_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
        return self.model

    def build(self, rows: list[tuple[str, str]], output: Path) -> None:
        """Build FAISS cosine index for mock TM2 titles."""
        import faiss
        import numpy as np
        vectors = self._load_model().encode([title for _, title in rows], normalize_embeddings=True)
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(np.asarray(vectors, dtype="float32"))
        self.codes = [code for code, _ in rows]
        faiss.write_index(self.index, str(output))
        np.save(output.with_suffix(".codes.npy"), np.asarray(self.codes, dtype=object), allow_pickle=True)

    def query(self, text: str, k: int = 3) -> list[tuple[str, float]]:
        if self.index is None:
            return []
        import numpy as np
        vector = self._load_model().encode([text], normalize_embeddings=True)
        distances, positions = self.index.search(np.asarray(vector, dtype="float32"), k)
        return [(self.codes[pos], float(score)) for score, pos in zip(distances[0], positions[0]) if pos >= 0]
