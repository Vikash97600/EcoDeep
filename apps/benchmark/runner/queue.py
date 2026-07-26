from apps.benchmark.models import BenchmarkJob, BenchmarkStatusChoices

class JobQueueManager:
    """Manages state transitions and ordering of enqueued benchmark jobs."""

    @staticmethod
    def get_next_pending_job(session):
        return session.jobs.filter(status=BenchmarkStatusChoices.PENDING).order_by('priority', 'created_at').first()

    @staticmethod
    def update_job_status(job, status, error_log=""):
        job.status = status
        if error_log:
            job.error_log = error_log
        job.save()
        return job
