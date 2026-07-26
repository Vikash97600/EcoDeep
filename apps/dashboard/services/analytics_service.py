from django.db.models import Avg, Max, Min
from apps.benchmark.models import BenchmarkResult

class AnalyticsService:
    """Generates structured chart datasets for Chart.js interactive visualizations."""

    @staticmethod
    def get_chart_telemetry():
        results = BenchmarkResult.objects.select_related('library_version__library').order_by('-created_at')[:10]

        labels = [r.library_version.library.library_name for r in results]
        execution_times = [float(r.execution_time) for r in results]
        energies = [float(r.energy) for r in results]
        memories = [float(r.peak_memory) for r in results]
        cpus = [float(r.average_cpu) for r in results]
        green_scores = [float(r.green_score) for r in results]

        return {
            'labels': labels,
            'execution_times': execution_times,
            'energies': energies,
            'memories': memories,
            'cpus': cpus,
            'green_scores': green_scores
        }
