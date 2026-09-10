from apps.benchmark.models import BenchmarkResult


class RepositoryService:
    """Service querying and filtering the research telemetry repository."""

    @staticmethod
    def filter_repository(category_id=None, task_id=None, search_query=None):
        queryset = BenchmarkResult.objects.select_related(
            'session', 'library_version__library', 'task', 'dataset'
        ).order_by('-created_at')

        if category_id:
            queryset = queryset.filter(task__category_id=category_id)
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        if search_query:
            queryset = queryset.filter(library_version__library__library_name__icontains=search_query)

        return queryset
