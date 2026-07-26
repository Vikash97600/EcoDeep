from apps.benchmark.models import BenchmarkResult

class ResultCollector:
    """Formats and records execution state metadata into BenchmarkResult database records."""

    @staticmethod
    def collect_and_store(session, job, remarks="Executed via BenchmarkRunner Pipeline"):
        result = BenchmarkResult.objects.create(
            session=session,
            library_version=job.library_version,
            task=job.task,
            dataset=job.task.dataset,
            iterations=job.task.iterations,
            remarks=remarks
        )
        return result
