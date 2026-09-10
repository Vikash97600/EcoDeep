from apps.mcdm.services.normalization_service import NormalizationService


class WPMService:
    """Evaluates candidates using the Weighted Product Model (WPM)."""

    @staticmethod
    def calculate_wpm(normalized_matrix: list[dict[str, float]], weights: dict[str, float]) -> list[dict[str, float]]:
        """Calculates WPM utility score for each candidate: P_i = prod(r_ij ^ w_j)."""
        results = []
        for row in normalized_matrix:
            product = 1.0
            for k in NormalizationService.CRITERIA_KEYS:
                val = max(1e-6, row.get(k, 0.0))
                w = weights.get(k, 0.0)
                product *= (val ** w)

            results.append({
                'library_id': row.get('library_id'),
                'library_name': row.get('library_name'),
                'wpm_score': round(product, 5)
            })

        results.sort(key=lambda x: x['wpm_score'], reverse=True)
        return results
