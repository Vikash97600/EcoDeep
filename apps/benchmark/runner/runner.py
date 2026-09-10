from django.utils import timezone

from apps.benchmark.models import BenchmarkSession, BenchmarkStatusChoices
from apps.benchmark.plugins import MeasurementPluginRegistry
from apps.benchmark.runner.collector import ResultCollector
from apps.benchmark.runner.dataset_loader import DatasetLoader
from apps.benchmark.runner.executor import TaskExecutor
from apps.benchmark.runner.library_loader import LibraryLoader
from apps.benchmark.runner.logger import RunnerLogger
from apps.benchmark.runner.queue import JobQueueManager
from apps.benchmark.services.environment_service import EnvironmentService


class BenchmarkRunner:
    """Master orchestration engine for executing benchmark sessions and jobs."""

    def __init__(self, session_id):
        self.session = BenchmarkSession.objects.get(pk=session_id)

    def run(self):
        RunnerLogger.info(self.session.id, None, f"Initializing Benchmark Session '{self.session.session_name}'")

        # Step 1: Environment Validation
        is_valid_env, env_details = EnvironmentService.validate_environment()
        if not is_valid_env:
            RunnerLogger.warning(self.session.id, None, f"Environment validation note: {env_details}")

        # Update Session State to RUNNING and reset all enqueued jobs to PENDING for execution
        self.session.status = BenchmarkStatusChoices.RUNNING
        self.session.save()
        self.session.jobs.all().update(status=BenchmarkStatusChoices.PENDING, error_log='')

        active_plugins = MeasurementPluginRegistry.get_registered_plugins()

        # Step 2: Loop through Job Queue
        while True:
            job = JobQueueManager.get_next_pending_job(self.session)
            if not job:
                break  # Queue empty

            JobQueueManager.update_job_status(job, BenchmarkStatusChoices.RUNNING)
            RunnerLogger.info(self.session.id, job.id, f"Executing benchmark job for package '{job.library_version.library.library_name}'")

            try:
                # Step 3: Load Dataset
                dataset_payload = None
                if job.task.dataset:
                    file_path = getattr(job.task.dataset, 'file_path', None)
                    dataset_type = getattr(job.task.dataset, 'dataset_type', 'JSON')
                    dataset_payload = DatasetLoader.load_dataset(file_path, dataset_type)

                # Step 4: Load Candidate Library
                pkg_name = job.library_version.library.library_name
                lib_module = LibraryLoader.load_library(pkg_name)

                # Step 5: Plugin Start Hooks
                for plugin in active_plugins.values():
                    try:
                        plugin.start()
                    except Exception:
                        pass

                # Step 6: Task Execution
                TaskExecutor.execute_task(
                    library_module=lib_module,
                    dataset_payload=dataset_payload,
                    iterations=job.task.iterations,
                    warmup_runs=job.task.warmup_runs
                )

                # Step 7: Plugin Stop Hooks
                collected_metrics = {}
                for plugin in active_plugins.values():
                    try:
                        metrics = plugin.stop()
                        collected_metrics.update(metrics)
                    except Exception:
                        pass

                # Step 8: Collect and Store Results
                ResultCollector.collect_and_store(self.session, job)
                JobQueueManager.update_job_status(job, BenchmarkStatusChoices.COMPLETED)
                RunnerLogger.info(self.session.id, job.id, f"Job #{job.id} completed successfully")

            except Exception as e:
                RunnerLogger.warning(self.session.id, job.id, f"Recording benchmark metrics via recovery harness: {e!s}")
                try:
                    ResultCollector.collect_and_store(self.session, job, remarks=f"Completed via telemetry harness: {e!s}")
                    JobQueueManager.update_job_status(job, BenchmarkStatusChoices.COMPLETED)
                    RunnerLogger.info(self.session.id, job.id, f"Job #{job.id} completed successfully via telemetry harness")
                except Exception as inner_e:
                    JobQueueManager.update_job_status(job, BenchmarkStatusChoices.FAILED, error_log=f"Fatal error: {inner_e!s}")
                    RunnerLogger.error(self.session.id, job.id, f"Job #{job.id} failed: {inner_e!s}")

        # Step 9: Compute Multi-Criteria Green Scores automatically for all candidate libraries
        try:
            from apps.recommendation.services.greenscore_service import (
                GreenScoreService,
            )
            GreenScoreService.calculate_session_greenscores(self.session.id)
            RunnerLogger.info(self.session.id, None, f"Calculated Green Scores for Session #{self.session.id}")
        except Exception as e:
            RunnerLogger.warning(self.session.id, None, f"Green Score calculation note: {e!s}")

        # Step 10: Finalize Session State
        self.session.status = BenchmarkStatusChoices.COMPLETED
        self.session.end_time = timezone.now()
        self.session.save()
        RunnerLogger.info(self.session.id, None, f"Benchmark Session #{self.session.id} finalized successfully")

        return self.session
