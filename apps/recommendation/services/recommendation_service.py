from apps.benchmark.models import BenchmarkResult, BenchmarkTask
from apps.libraries.models import Library
from apps.recommendation.models import (
    RecommendationItem,
    RecommendationRecord,
)
from apps.recommendation.services.constraint_service import ConstraintService
from apps.recommendation.services.recommendation_confidence_service import (
    RecommendationConfidenceService,
)
from apps.recommendation.services.recommendation_explanation_service import (
    RecommendationExplanationService,
)
from apps.recommendation.services.recommendation_ranking_service import (
    RecommendationRankingService,
)
from apps.recommendation.services.similarity_service import SimilarityService


class RecommendationService:
    """Master orchestrator for candidate discovery, constraint filtering, ranking, and explanation."""

    @staticmethod
    def generate_recommendation(target_library_id, task_id, profile_type='BEST_OVERALL', user=None):
        target_lib = Library.objects.get(pk=target_library_id)
        task = BenchmarkTask.objects.get(pk=task_id)

        # 1. Discover candidates via SimilarityService
        candidates = SimilarityService.get_equivalent_libraries(target_lib)

        # Include target library itself for baseline comparative analysis
        candidate_libs = list(candidates) + [target_lib]

        # 2. Filter candidates via ConstraintService
        valid_libs = ConstraintService.filter_candidates(candidate_libs)

        # 3. Retrieve latest BenchmarkResult for valid candidates on this task
        results = BenchmarkResult.objects.filter(
            library_version__library__in=valid_libs,
            task=task
        ).select_related('library_version__library', 'task').order_by('-created_at')

        # Map to latest result per library
        latest_results_map = {}
        for r in results:
            lib_id = r.library_version.library.id
            if lib_id not in latest_results_map:
                latest_results_map[lib_id] = r

        evaluated_results = list(latest_results_map.values())
        target_result = latest_results_map.get(target_lib.id)

        # 4. Rank candidates using selected profile
        ranked_results = RecommendationRankingService.rank_candidates(evaluated_results, profile_type=profile_type)

        # 5. Persist RecommendationRecord & RecommendationItems
        rec_record = RecommendationRecord.objects.create(
            user=user,
            target_library=target_lib,
            task=task,
            recommendation_profile=profile_type,
            candidates_evaluated_count=len(ranked_results)
        )

        items = []
        for index, r in enumerate(ranked_results, start=1):
            exp_text = RecommendationExplanationService.generate_recommendation_explanation(
                target_result, r, profile_type
            )
            conf_score = RecommendationConfidenceService.calculate_confidence(r)

            item = RecommendationItem.objects.create(
                record=rec_record,
                recommended_version=r.library_version,
                rank=index,
                green_score=r.green_score,
                confidence_score=conf_score,
                explanation_text=exp_text,
                is_top_choice=(index == 1)
            )
            items.append(item)

        return rec_record
