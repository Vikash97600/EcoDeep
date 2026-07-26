from apps.benchmark.services.orchestrator.queue_service import QueueService
from apps.benchmark.services.orchestrator.worker_service import WorkerService
from apps.benchmark.services.orchestrator.resource_monitor_service import ResourceMonitorService
from apps.benchmark.runner.runner import BenchmarkRunner

class SchedulerService:
    """Master Benchmark Orchestrator checking worker availability and executing queued jobs."""

    @staticmethod
    def dispatch_next_job():
        """Dispatches next queued job if host CPU and RAM resources are below 85% safety limits."""
        # 1. Register worker node heartbeat
        worker = WorkerService.register_current_node()

        # 2. Check host resources
        is_safe, cpu_pct, ram_pct = ResourceMonitorService.is_host_resource_available()
        if not is_safe:
            return False, f"Host resource load too high (CPU: {cpu_pct}%, RAM: {ram_pct}%). Delaying dispatch."

        # 3. Fetch next priority job
        job = QueueService.get_next_job()
        if not job:
            return False, "No pending benchmark jobs in queue."

        # 4. Trigger BenchmarkRunner execution
        runner = BenchmarkRunner(session_id=job.session.id)
        runner.run()
        return True, f"Successfully dispatched and executed Session #{job.session.id} (Job #{job.id})."
