from typing import List, Dict
from apps.mcdm.services.normalization_service import NormalizationService

class WSMService:
    """Evaluates candidates using the Weighted Sum Model (WSM)."""

    @staticmethod
    def calculate_wsm(normalized_matrix: List[Dict[str, float]], weights: Dict[str, float]) -> List[Dict[str, float]]:
        """Calculates WSM utility score for each candidate: S_i = sum(w_j * r_ij)."""
        results = []
        for row in normalized_matrix:
            score = sum(weights.get(k, 0.0) * row.get(k, 0.0) for k in NormalizationService.CRITERIA_KEYS)
            results.append({
                'library_id': row.get('library_id'),
                'library_name': row.get('library_name'),
                'wsm_score': round(score, 5)
            })

        results.sort(key=lambda x: x['wsm_score'], reverse=True)
        return results
