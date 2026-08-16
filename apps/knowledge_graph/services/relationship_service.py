from apps.libraries.models import Library, SimilarLibraryMapping
from apps.knowledge_graph.models import SimilarityScore, RelationshipTypeChoices
from apps.knowledge_graph.services.similarity_service import SimilarityService

class RelationshipService:
    """Discovers and establishes cross-library relationships and maps them to SimilarLibraryMapping."""

    @staticmethod
    def discover_all_relationships(min_similarity_threshold: float = 0.35) -> list:
        """Iterates over all library combinations, calculates similarities, and persists discovered edges."""
        libraries = list(Library.objects.select_related('category', 'programming_language').all())
        discovered = []

        for i in range(len(libraries)):
            for j in range(i + 1, len(libraries)):
                lib_a = libraries[i]
                lib_b = libraries[j]

                score_obj = SimilarityService.compute_library_pair_similarity(lib_a, lib_b)
                if score_obj.composite_similarity >= min_similarity_threshold:
                    discovered.append(score_obj)

                    # Also populate or link with core SimilarLibraryMapping
                    SimilarLibraryMapping.objects.get_or_create(
                        source_library=lib_a,
                        target_library=lib_b,
                        defaults={
                            'similarity_type': 'DIRECT' if score_obj.composite_similarity >= 0.75 else 'FUNCTIONAL',
                            'similarity_score': round(score_obj.composite_similarity, 2),
                            'reason': f"Auto-discovered via NLP Pipeline (Composite Similarity: {score_obj.composite_similarity:.2f})"
                        }
                    )

        return discovered
