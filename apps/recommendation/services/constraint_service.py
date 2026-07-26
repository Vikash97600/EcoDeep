from apps.libraries.models import StatusChoices

class ConstraintService:
    """Filters candidate libraries according to compatibility, license, and benchmark availability constraints."""

    @staticmethod
    def filter_candidates(candidate_libraries, required_language=None):
        filtered = []
        for lib in candidate_libraries:
            if lib.status != StatusChoices.ACTIVE:
                continue
            if required_language and lib.programming_language != required_language:
                continue
            filtered.append(lib)
        return filtered
