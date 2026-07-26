class ValidationService:
    """Validates raw and processed benchmark telemetry metrics prior to repository storage."""

    @staticmethod
    def validate_metrics(execution_time_ms, cpu_usage_pct, peak_memory_mb, energy_joules):
        errors = []
        if execution_time_ms is None or execution_time_ms < 0:
            errors.append("Execution time must be a non-negative decimal value.")
        if cpu_usage_pct is None or cpu_usage_pct < 0 or cpu_usage_pct > 1000:
            errors.append("CPU utilization percentage out of valid bounds (0-1000%).")
        if peak_memory_mb is None or peak_memory_mb < 0:
            errors.append("Peak memory allocation must be a non-negative value.")
        if energy_joules is None or energy_joules < 0:
            errors.append("Energy consumption in Joules cannot be negative.")

        is_valid = len(errors) == 0
        return is_valid, errors
