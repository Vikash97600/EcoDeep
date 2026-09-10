from abc import ABC, abstractmethod


class BaseScoringStrategy(ABC):
    """Abstract Strategy interface for multi-criteria decision models."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def compute_scores(self, normalized_matrix, weight_dict) -> dict:
        """Returns map of result_id -> raw score (0.0 - 1.0)."""
