from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddings(ABC):
    """Abstract embeddings provider interface."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return embedding dimensionality (constant for a given model)."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of input strings.

        Returns:
            List[List[float]]: One embedding per input, each a fixed-length float vector.
        """