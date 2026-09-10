from django.utils import timezone

from apps.benchmark.models import (
    BenchmarkResult,
    BenchmarkSession,
    BenchmarkStatusChoices,
)
from apps.benchmark.plugins import MeasurementPluginRegistry


class BenchmarkRunnerService:
    """Orchestrates job execution and plugin hooks without hardcoding physical measurements."""

    @staticmethod
    def execute_session(session_id):
        session = BenchmarkSession.objects.get(pk=session_id)
        session.status = BenchmarkStatusChoices.RUNNING
        session.save()

        jobs = session.jobs.filter(status=BenchmarkStatusChoices.PENDING).order_by('priority')
        active_plugins = MeasurementPluginRegistry.get_registered_plugins()

        for job in jobs:
            job.status = BenchmarkStatusChoices.RUNNING
            job.save()

            try:
                # Trigger Plugin start hooks
                for plugin in active_plugins.values():
                    plugin.start()

                # Workload loop execution (placeholder harness interface)
                # Physical time/energy counters will be measured by plugins in future prompts

                # Trigger Plugin stop hooks
                collected_metrics = {}
                for plugin in active_plugins.values():
                    metrics = plugin.stop()
                    collected_metrics.update(metrics)

                # Record BenchmarkResult metadata
                BenchmarkResult.objects.create(
                    session=session,
                    library_version=job.library_version,
                    task=job.task,
                    dataset=job.task.dataset,
                    iterations=job.task.iterations,
                    remarks="Executed cleanly via BenchmarkRunner Harness"
                )

                job.status = BenchmarkStatusChoices.COMPLETED
                job.save()

            except Exception as e:
                job.status = BenchmarkStatusChoices.FAILED
                job.error_log = str(e)
                job.save()

        session.status = BenchmarkStatusChoices.COMPLETED
        session.end_time = timezone.now()
        session.save()
        return session
