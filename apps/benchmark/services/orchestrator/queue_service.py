from apps.benchmark.models import BenchmarkJob, BenchmarkStatusChoices


class QueueService:
    """Manages priority execution queues (FIFO, Priority, Retry queues)."""

    @staticmethod
    def get_pending_queue():
        """Returns pending jobs ordered by priority (highest first) and creation timestamp."""
        return BenchmarkJob.objects.filter(
            status=BenchmarkStatusChoices.PENDING
        ).select_related('session', 'library_version__library', 'task').order_by('-priority', 'created_at')

    @staticmethod
    def get_next_job():
        """Fetches the next highest priority pending job from the execution queue."""
        return QueueService.get_pending_queue().first()
