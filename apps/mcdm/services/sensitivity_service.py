from apps.mcdm.models import MCDMEvaluationRun, SensitivityAuditReport
from apps.mcdm.services.topsis_service import TOPSService


class SensitivityService:
    """Evaluates rank stability under weight perturbations using Spearman's rank correlation."""

    @staticmethod
    def calculate_spearman_rho(ranks_a: list[int], ranks_b: list[int]) -> float:
        """Calculates Spearman's rank correlation coefficient rho."""
        n = len(ranks_a)
        if n <= 1:
            return 1.0

        d_sq_sum = sum((ra - rb) ** 2 for ra, rb in zip(ranks_a, ranks_b))
        rho = 1.0 - ((6.0 * d_sq_sum) / (n * (n ** 2 - 1)))
        return round(max(-1.0, min(1.0, rho)), 4)

    @staticmethod
    def audit_ranking_sensitivity(evaluation_run: MCDMEvaluationRun, criterion_to_perturb: str = 'energy_joules', perturbation_pct: float = 20.0) -> SensitivityAuditReport:
        """Perturbs a criterion weight and measures rank reversals and Spearman's rho."""
        profile = evaluation_run.weight_profile
        base_weights = {
            'energy_joules': profile.weight_energy,
            'execution_time_ms': profile.weight_execution_time,
            'cpu_utilization_pct': profile.weight_cpu,
            'ram_rss_mb': profile.weight_memory,
            'co2_emissions_g': profile.weight_co2
        }

        # Perturb weight
        perturbed_weights = base_weights.copy()
        factor = 1.0 + (perturbation_pct / 100.0)
        perturbed_weights[criterion_to_perturb] = max(0.01, base_weights.get(criterion_to_perturb, 0.2) * factor)

        # Normalize perturbed weights
        tot = sum(perturbed_weights.values())
        perturbed_weights = {k: v / tot for k, v in perturbed_weights.items()}

        raw_matrix = evaluation_run.decision_matrix_json.get('candidates', [])
        if not raw_matrix:
            return SensitivityAuditReport.objects.create(
                evaluation_run=evaluation_run,
                perturbed_criterion=criterion_to_perturb,
                perturbation_pct=perturbation_pct,
                rank_reversals_count=0,
                spearman_rho=1.0,
                is_robust=True,
                notes="Decision matrix was empty."
            )

        # Base ranking
        base_results = TOPSService.calculate_topsis(raw_matrix, base_weights)
        base_order = {item['library_id']: idx + 1 for idx, item in enumerate(base_results)}

        # Perturbed ranking
        pert_results = TOPSService.calculate_topsis(raw_matrix, perturbed_weights)
        pert_order = {item['library_id']: idx + 1 for idx, item in enumerate(pert_results)}

        # Compute rank differences and reversals
        ranks_base = [base_order[lib_id] for lib_id in base_order]
        ranks_pert = [pert_order[lib_id] for lib_id in base_order]

        rho = SensitivityService.calculate_spearman_rho(ranks_base, ranks_pert)
        reversals = sum(1 for rb, rp in zip(ranks_base, ranks_pert) if rb != rp)
        is_robust = rho >= 0.85

        notes = (
            f"Perturbing '{criterion_to_perturb}' by {perturbation_pct:+.1f}% resulted in {reversals} rank adjustments "
            f"with a Spearman correlation of rho={rho:.4f}. "
            f"{'The ranking is mathematically robust.' if is_robust else 'Warning: Ranking exhibits sensitivity to weight changes.'}"
        )

        return SensitivityAuditReport.objects.create(
            evaluation_run=evaluation_run,
            perturbed_criterion=criterion_to_perturb,
            perturbation_pct=perturbation_pct,
            rank_reversals_count=reversals,
            spearman_rho=rho,
            is_robust=is_robust,
            notes=notes
        )
