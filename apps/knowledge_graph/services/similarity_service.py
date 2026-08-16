import math
from typing import Dict, List, Tuple
from apps.libraries.models import Library
from apps.knowledge_graph.models import SimilarityScore, RelationshipTypeChoices
from apps.knowledge_graph.services.embedding_service import EmbeddingService
from apps.knowledge_graph.services.nlp_service import NLPService

class SimilarityService:
    """Calculates Cosine, Jaccard, and Composite similarity scores across candidate library pairs."""

    @staticmethod
    def calculate_cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """Calculates cosine similarity between two normalized sparse term vectors."""
        if not vec_a or not vec_b:
            return 0.0

        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        dot_product = sum(vec_a[k] * vec_b[k] for k in common_keys)
        
        mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
        mag_b = math.sqrt(sum(v * v for v in vec_b.values()))

        if mag_a == 0 or mag_b == 0:
            return 0.0

        cosine = dot_product / (mag_a * mag_b)
        return round(min(1.0, max(0.0, cosine)), 4)

    @staticmethod
    def calculate_jaccard_similarity(tokens_a: List[str], tokens_b: List[str]) -> float:
        """Calculates Jaccard token overlap similarity."""
        set_a = set(tokens_a)
        set_b = set(tokens_b)
        if not set_a or not set_b:
            return 0.0

        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return round(intersection / union, 4) if union > 0 else 0.0

    @staticmethod
    def compute_library_pair_similarity(lib_a: Library, lib_b: Library) -> SimilarityScore:
        """Computes comprehensive composite similarity between two libraries."""
        emb_a = EmbeddingService.generate_library_embedding(lib_a)
        emb_b = EmbeddingService.generate_library_embedding(lib_b)

        cosine_sim = SimilarityService.calculate_cosine_similarity(emb_a.vector_json, emb_b.vector_json)

        tokens_a = NLPService.tokenize(f"{lib_a.library_name} {lib_a.description}")
        tokens_b = NLPService.tokenize(f"{lib_b.library_name} {lib_b.description}")
        jaccard_sim = SimilarityService.calculate_jaccard_similarity(tokens_a, tokens_b)

        # Category match boost
        cat_match = 1.0 if (lib_a.category and lib_b.category and lib_a.category == lib_b.category) else 0.0
        
        # Language compatibility check
        lang_match = 1.0 if (lib_a.programming_language == lib_b.programming_language) else 0.5

        # Composite formula: 50% Cosine + 20% Jaccard + 30% Category
        composite = (0.50 * cosine_sim + 0.20 * jaccard_sim + 0.30 * cat_match) * lang_match
        composite = round(min(1.0, max(0.0, composite)), 4)

        # Classify relationship type
        if composite >= 0.75:
            rel_type = RelationshipTypeChoices.DIRECT_REPLACEMENT
        elif composite >= 0.40:
            rel_type = RelationshipTypeChoices.FUNCTIONAL_ALTERNATIVE
        else:
            rel_type = RelationshipTypeChoices.COMPETES_WITH

        score_obj, created = SimilarityScore.objects.update_or_create(
            source_library=lib_a,
            target_library=lib_b,
            defaults={
                'cosine_similarity': cosine_sim,
                'jaccard_similarity': jaccard_sim,
                'composite_similarity': composite,
                'is_discovered': True,
                'relationship_type': rel_type
            }
        )
        return score_obj
