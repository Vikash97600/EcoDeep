import logging

runner_logger = logging.getLogger('benchmark.runner')

class RunnerLogger:
    """Structured logging utility for benchmark execution steps."""

    @staticmethod
    def info(session_id, job_id, message):
        runner_logger.info(f"[Session #{session_id} | Job #{job_id}] {message}")

    @staticmethod
    def warning(session_id, job_id, message):
        runner_logger.warning(f"[Session #{session_id} | Job #{job_id}] {message}")

    @staticmethod
    def error(session_id, job_id, message, exc_info=False):
        runner_logger.error(f"[Session #{session_id} | Job #{job_id}] {message}", exc_info=exc_info)
