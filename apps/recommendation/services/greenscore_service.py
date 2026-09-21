from apps.benchmark.models import BenchmarkResult, BenchmarkSession
from apps.recommendation.models import (
    GreenScore,
    HistoricalGreenScore,
    ScoreCategoryChoices,
    WeightProfile,
)
from apps.recommendation.services.confidence_service import ConfidenceService
from apps.recommendation.services.explanation_service import ExplanationService
from apps.recommendation.services.normalization_service import NormalizationService
from apps.recommendation.services.strategies.topsis import TopsisStrategy
from apps.recommendation.services.strategies.weighted_product import (
    WeightedProductStrategy,
)
from apps.recommendation.services.strategies.weighted_sum import WeightedSumStrategy


class GreenScoreService:
    """Master orchestrator for multi-criteria normalization, MCDM scoring, and ranking."""

    STRATEGIES = {
        'WSM': WeightedSumStrategy(),
        'WPM': WeightedProductStrategy(),
        'TOPSIS': TopsisStrategy(),
    }

    @staticmethod
    def calculate_session_greenscores(session_id, strategy_name='TOPSIS', profile_name=None):
        session = BenchmarkSession.objects.get(pk=session_id)
        results = BenchmarkResult.objects.filter(session=session).select_related('library_version__library', 'task', 'dataset')

        if not results.exists():
            return []

        profile = None
        if profile_name:
            profile = WeightProfile.objects.filter(profile_name=profile_name).first()
        if not profile:
            profile, _ = WeightProfile.objects.get_or_create(
                profile_name='Balanced Default',
                defaults={
                    'description': 'Balanced 30% Time, 20% CPU, 20% RAM, 20% Energy, 10% CO2',
                    'weight_execution_time': 0.30,
                    'weight_cpu_usage': 0.20,
                    'weight_peak_memory': 0.20,
                    'weight_energy': 0.20,
                    'weight_co2': 0.10,
                    'is_default': True
                }
            )

        # 1. Group results by task for context-aware task-level evaluation
        task_groups = {}
        for r in results:
            task_id = r.task_id if r.task else 0
            task_groups.setdefault(task_id, []).append(r)

        strategy = GreenScoreService.STRATEGIES.get(strategy_name, TopsisStrategy())
        weight_dict = {
            'weight_execution_time': profile.weight_execution_time,
            'weight_cpu_usage': profile.weight_cpu_usage,
            'weight_peak_memory': profile.weight_peak_memory,
            'weight_energy': profile.weight_energy,
            'weight_co2': profile.weight_co2
        }

        greenscore_objects = []

        for task_id, task_results in task_groups.items():
            results_data = []
            for r in task_results:
                results_data.append({
                    'result_id': r.id,
                    'execution_time': float(r.execution_time),
                    'cpu_usage': float(r.average_cpu),
                    'peak_memory': float(r.peak_memory),
                    'energy': float(r.energy),
                    'co2': float(r.co2)
                })

            # 2. Normalize metrics per task (continuous magnitude scaling)
            norm_matrix = NormalizationService.normalize_results(results_data)

            # 3. Apply MCDM Strategy per task
            raw_scores = strategy.compute_scores(norm_matrix, weight_dict)

            # 4. Scale & Persist GreenScore objects
            for r in task_results:
                raw_score = raw_scores.get(r.id, 0.5)
                final_score = round(raw_score * 100.0, 2)

                if final_score >= 90.0:
                    cat = ScoreCategoryChoices.EXCELLENT
                elif final_score >= 70.0:
                    cat = ScoreCategoryChoices.GOOD
                elif final_score >= 50.0:
                    cat = ScoreCategoryChoices.AVERAGE
                else:
                    cat = ScoreCategoryChoices.NEEDS_IMPROVEMENT

                conf_score = ConfidenceService.calculate_confidence(r.iterations, r.raw_samples.count())
                exp_text = ExplanationService.generate_explanation(
                    r.library_version.library.library_name, final_score, cat, r, profile
                )

                # Update or Create GreenScore
                gs, _ = GreenScore.objects.update_or_create(
                    result=r,
                    defaults={
                        'library_version': r.library_version,
                        'session': session,
                        'task': r.task,
                        'weight_profile': profile,
                        'strategy_used': strategy.name,
                        'score': final_score,
                        'category': cat,
                        'confidence_score': conf_score,
                        'explanation': exp_text
                    }
                )

                # Update Green Score on BenchmarkResult for fast queries
                r.green_score = final_score
                r.save()

                # Record Historical Entry
                HistoricalGreenScore.objects.create(
                    library_version=r.library_version,
                    task=r.task,
                    score=final_score,
                    strategy_used=strategy.name
                )

                greenscore_objects.append(gs)

        return greenscore_objects
