from apps.benchmark.models import BenchmarkResult

class RecommendationRankingService:
    """Ranks candidate recommendation results based on selected profile criteria."""

    @staticmethod
    def rank_candidates(benchmark_results, profile_type='BEST_OVERALL'):
        results = list(benchmark_results)

        if profile_type == 'MOST_ENERGY_EFFICIENT':
            results.sort(key=lambda r: float(r.energy))
        elif profile_type == 'FASTEST':
            results.sort(key=lambda r: float(r.execution_time))
        elif profile_type == 'LOWEST_MEMORY':
            results.sort(key=lambda r: float(r.peak_memory))
        elif profile_type == 'LOWEST_CPU':
            results.sort(key=lambda r: float(r.average_cpu))
        elif profile_type == 'LOWEST_CO2':
            results.sort(key=lambda r: float(r.co2))
        else:  # BEST_OVERALL
            results.sort(key=lambda r: float(r.green_score), reverse=True)

        return results
