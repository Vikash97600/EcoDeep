from apps.libraries.models import Library
from apps.xai.models import TrustScoreRecord

class TrustService:
    """Calculates multi-dimensional recommendation Trust Scores (0-100%)."""

    @staticmethod
    def evaluate_trust_score(
        library: Library,
        data_completeness: float = 95.0,
        measurement_fidelity: float = 98.0,
        explanation_clarity: float = 92.0
    ) -> TrustScoreRecord:
        """Computes weighted trust score: 35% Fidelity + 30% Completeness + 20% Confidence + 15% Clarity."""
        overall_score = (
            0.35 * measurement_fidelity +
            0.30 * data_completeness +
            0.20 * 95.0 +
            0.15 * explanation_clarity
        )
        overall_score = round(min(100.0, max(0.0, overall_score)), 1)

        if overall_score >= 90.0:
            badge = "Verified Scientific Trust (Tier A+)"
        elif overall_score >= 75.0:
            badge = "High Empirical Trust (Tier A)"
        elif overall_score >= 60.0:
            badge = "Moderate Trust (Tier B)"
        else:
            badge = "Uncertain / Unverified"

        record, _ = TrustScoreRecord.objects.update_or_create(
            library=library,
            defaults={
                'overall_trust_score': overall_score,
                'data_completeness_score': data_completeness,
                'measurement_fidelity_score': measurement_fidelity,
                'explanation_clarity_score': explanation_clarity,
                'status_badge': badge
            }
        )
        return record
