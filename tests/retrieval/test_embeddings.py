import numpy as np
import pytest

from app.retrieval.embeddings import BGEEmbedder


class Model:
    def encode(self, texts, **kwargs):
        return np.ones((len(texts), 3), dtype="float32")


def test_embedder_rejects_wrong_dimension() -> None:
    with pytest.raises(ValueError, match="Expected embedding dimension"):
        BGEEmbedder(dimensions=1024, model=Model()).encode(["text"])