import math
import random

from apps.benchmark.models import BenchmarkStatusChoices, JobRetryLog


class RetryService:
    """Manages job retry policies and exponential backoff calculations."""

    BASE_DELAY_SECONDS = 5.0

    @staticmethod
    def calculate_backoff_delay(attempt_number):
        """Calculates exponential backoff delay: base_delay * 2^(attempt-1) + jitter."""
        delay = RetryService.BASE_DELAY_SECONDS * math.pow(2, attempt_number - 1)
        jitter = random.uniform(0.0, 1.0)
        return round(delay + jitter, 2)

    @staticmethod
    def handle_job_failure(job, exception):
        """Evaluates whether to retry a failed job or mark as permanently failed."""
        job.retry_count += 1
        attempt = job.retry_count

        backoff = RetryService.calculate_backoff_delay(attempt)
        JobRetryLog.objects.create(
            job=job,
            attempt_number=attempt,
            backoff_delay_seconds=backoff,
            exception_trace=str(exception)
        )

        if job.retry_count < job.max_retries:
            job.status = BenchmarkStatusChoices.PENDING
            job.save()
            return True, f"Re-queued for attempt {attempt + 1}/{job.max_retries} with {backoff}s backoff."
        else:
            job.status = BenchmarkStatusChoices.FAILED
            job.error_log = f"Failed permanently after {job.retry_count} retries. Exception: {exception!s}"
            job.save()
            return False, "Max retry limit reached. Marked job as FAILED."
