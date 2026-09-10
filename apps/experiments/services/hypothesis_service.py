from apps.experiments.models import (
    HypothesisTestChoices,
    HypothesisTestResult,
    ScientificDataset,
)
from apps.experiments.services.statistics_service import StatisticsService
from apps.libraries.models import Library


class HypothesisService:
    """Executes formal hypothesis testing and effect size quantification between library pairs."""

    @staticmethod
    def evaluate_library_pair(dataset: ScientificDataset, baseline_lib: Library, target_lib: Library, metric_name: str = 'execution_time_ms'):
        """Evaluates null vs alternative hypothesis between baseline and target library."""
        obs_a = list(dataset.observations.filter(library=baseline_lib, is_warmup=False, is_outlier=False).values_list(metric_name, flat=True))
        obs_b = list(dataset.observations.filter(library=target_lib, is_warmup=False, is_outlier=False).values_list(metric_name, flat=True))

        if len(obs_a) < 2 or len(obs_b) < 2:
            return None

        ttest_res = StatisticsService.compute_two_sample_ttest(obs_a, obs_b)
        effect_res = StatisticsService.compute_cohens_d(obs_a, obs_b)
        
        reject_null = ttest_res['reject_null']
        p_val = ttest_res['p_value']
        d_val = effect_res['d_value']
        magnitude = effect_res['magnitude']

        if reject_null:
            if d_val > 0:
                interp = f"Statistically significant difference (p={p_val:.5f} < 0.05). {target_lib.library_name} exhibits lower {metric_name} with {magnitude} effect size (d={d_val:.2f})."
            else:
                interp = f"Statistically significant difference (p={p_val:.5f} < 0.05). {baseline_lib.library_name} exhibits lower {metric_name} with {magnitude} effect size (d={d_val:.2f})."
        else:
            interp = f"Failed to reject H0 (p={p_val:.5f} >= 0.05). No statistically significant difference observed in {metric_name} between {baseline_lib.library_name} and {target_lib.library_name}."

        result = HypothesisTestResult.objects.create(
            dataset=dataset,
            baseline_library=baseline_lib,
            target_library=target_lib,
            metric_name=metric_name,
            test_type=HypothesisTestChoices.STUDENT_T_TEST,
            test_statistic=ttest_res['t_stat'],
            p_value=p_val,
            alpha=0.05,
            reject_null_hypothesis=reject_null,
            effect_size_name="Cohen's d",
            effect_size_value=d_val,
            effect_size_magnitude=magnitude,
            interpretation=interp
        )
        return result
