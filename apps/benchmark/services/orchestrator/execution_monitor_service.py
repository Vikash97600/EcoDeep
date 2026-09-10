from apps.benchmark.models import BenchmarkJob, BenchmarkStatusChoices, WorkerNode


class ExecutionMonitorService:
    """Monitors real-time queue size, running jobs, and registered worker node health."""

    @staticmethod
    def get_orchestrator_summary():
        return {
            'pending_count': BenchmarkJob.objects.filter(status=BenchmarkStatusChoices.PENDING).count(),
            'running_count': BenchmarkJob.objects.filter(status=BenchmarkStatusChoices.RUNNING).count(),
            'completed_count': BenchmarkJob.objects.filter(status=BenchmarkStatusChoices.COMPLETED).count(),
            'failed_count': BenchmarkJob.objects.filter(status=BenchmarkStatusChoices.FAILED).count(),
            'worker_nodes': WorkerNode.objects.all(),
        }
