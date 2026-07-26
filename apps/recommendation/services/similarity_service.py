from apps.libraries.models import Library, SimilarLibraryMapping

class SimilarityService:
    """Discovers functionally equivalent candidate libraries matching target library queries."""

    @staticmethod
    def get_equivalent_libraries(target_library):
        """
        Retrieves candidates in the exact same functional category or explicitly mapped direct equivalents.
        """
        # 1. Direct explicit mappings
        mapped_ids = list(SimilarLibraryMapping.objects.filter(
            source_library=target_library
        ).values_list('target_library_id', flat=True))

        # 2. Category-level equivalents
        category_libraries = Library.objects.filter(
            category=target_library.category,
            programming_language=target_library.programming_language
        ).exclude(id=target_library.id)

        all_candidate_ids = set(mapped_ids).union(set(category_libraries.values_list('id', flat=True)))
        return Library.objects.filter(id__in=all_candidate_ids).select_related('category', 'programming_language')
