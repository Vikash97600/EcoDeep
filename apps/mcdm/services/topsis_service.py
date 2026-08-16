import math
from typing import List, Dict
from apps.mcdm.services.normalization_service import NormalizationService

class TOPSService:
    """Executes the Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS)."""

    @staticmethod
    def calculate_topsis(matrix: List[Dict[str, float]], weights: Dict[str, float]) -> List[Dict[str, float]]:
        """Calculates TOPSIS Euclidean separation distances and relative closeness coefficients."""
        if not matrix:
            return []

        # 1. Vector Normalization
        norm_matrix = NormalizationService.vector_normalize(matrix)

        # 2. Weighted Normalized Matrix
        weighted_matrix = []
        for row in norm_matrix:
            w_row = {'library_id': row['library_id'], 'library_name': row['library_name']}
            for k in NormalizationService.CRITERIA_KEYS:
                w_row[k] = row[k] * weights.get(k, 0.2)
            weighted_matrix.append(w_row)

        # 3. Determine Ideal (A*) and Negative Ideal (A-) Solutions
        # Note: All software efficiency metrics (Energy, Latency, CPU, RAM, CO2) are COST criteria (Lower is better)
        ideal_solution = {}
        negative_ideal_solution = {}

        for k in NormalizationService.CRITERIA_KEYS:
            col_vals = [r[k] for r in weighted_matrix]
            ideal_solution[k] = min(col_vals)
            negative_ideal_solution[k] = max(col_vals)

        # 4. Calculate Euclidean Separation Distances (S* and S-)
        results = []
        for r in weighted_matrix:
            s_plus = math.sqrt(sum((r[k] - ideal_solution[k]) ** 2 for k in NormalizationService.CRITERIA_KEYS))
            s_minus = math.sqrt(sum((r[k] - negative_ideal_solution[k]) ** 2 for k in NormalizationService.CRITERIA_KEYS))

            # 5. Calculate Relative Closeness C_i*
            total_dist = s_plus + s_minus
            closeness = (s_minus / total_dist) if total_dist > 0 else 0.5

            results.append({
                'library_id': r['library_id'],
                'library_name': r['library_name'],
                's_plus': round(s_plus, 5),
                's_minus': round(s_minus, 5),
                'closeness_coefficient': round(closeness, 4),
                'green_score': round(closeness * 100.0, 2)
            })

        # Rank descending by closeness coefficient (Green Score)
        results.sort(key=lambda x: x['closeness_coefficient'], reverse=True)
        return results
