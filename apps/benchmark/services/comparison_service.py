from apps.benchmark.models import BenchmarkResult

class ComparisonService:
    """Evaluates comparative energy and speed performance between candidate packages."""

    @staticmethod
    def compare_results(result_ids):
        results = list(BenchmarkResult.objects.filter(pk__in=result_ids).select_related(
            'library_version__library', 'task', 'dataset'
        ))

        if not results:
            return {}

        baseline = results[0]
        comparisons = []

        for r in results:
            time_delta_pct = round(((r.execution_time - baseline.execution_time) / baseline.execution_time) * 100, 2) if baseline.execution_time > 0 else 0.0
            energy_delta_pct = round(((r.energy - baseline.energy) / baseline.energy) * 100, 2) if baseline.energy > 0 else 0.0

            comparisons.append({
                'result_id': r.id,
                'package_version': str(r.library_version),
                'execution_time_ms': float(r.execution_time),
                'peak_memory_mb': float(r.peak_memory),
                'average_cpu_pct': float(r.average_cpu),
                'energy_joules': float(r.energy),
                'co2_grams': float(r.co2),
                'time_delta_pct': time_delta_pct,
                'energy_delta_pct': energy_delta_pct,
                'is_baseline': (r.id == baseline.id)
            })

        return {
            'task_name': baseline.task.task_name,
            'dataset_name': baseline.dataset.dataset_name,
            'baseline_package': str(baseline.library_version),
            'comparisons': comparisons
        }
