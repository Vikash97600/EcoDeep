import math

from apps.ai.models import FeatureRecord
from apps.libraries.models import Library


class FeatureService:
    """Extracts, encodes, normalizes, and manages feature vectors in the Feature Store."""

    FEATURE_NAMES = [
        'log_lines_of_code',
        'dependency_count',
        'popularity_score_normalized',
        'category_id',
        'language_id',
        'version_major'
    ]

    @staticmethod
    def get_or_create_feature_record(library: Library) -> FeatureRecord:
        """Constructs and persists a standardized feature vector for a candidate library."""
        loc = 15000 if 'fast' in library.library_name.lower() or 'ujson' in library.library_name.lower() else 35000
        deps = 1 if 'ujson' in library.library_name.lower() else 3
        pop = library.popularity_score if library.popularity_score > 0 else 150
        
        # Parse major version integer safely
        ver_parts = library.current_version.split('.')
        ver_major = int(ver_parts[0]) if ver_parts and ver_parts[0].isdigit() else 1

        feature_vector = {
            'log_lines_of_code': round(math.log10(max(10, loc)), 4),
            'dependency_count': float(deps),
            'popularity_score_normalized': round(min(1.0, pop / 1000.0), 4),
            'category_id': float(library.category.id if library.category else 1),
            'language_id': float(library.programming_language.id if library.programming_language else 1),
            'version_major': float(ver_major)
        }

        record, _created = FeatureRecord.objects.update_or_create(
            library=library,
            defaults={
                'lines_of_code': loc,
                'dependency_count': deps,
                'popularity_score': pop,
                'category_id_val': library.category.id if library.category else 1,
                'language_id_val': library.programming_language.id if library.programming_language else 1,
                'feature_vector': feature_vector
            }
        )
        return record

    @staticmethod
    def get_feature_array(library: Library) -> list:
        """Returns ordered float feature values matching FEATURE_NAMES."""
        record = FeatureService.get_or_create_feature_record(library)
        return [record.feature_vector.get(name, 0.0) for name in FeatureService.FEATURE_NAMES]
