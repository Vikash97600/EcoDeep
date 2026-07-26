class BenchmarkRunnerException(Exception):
    """Base exception for all Benchmark Runner execution failures."""
    pass

class DatasetLoadError(BenchmarkRunnerException):
    """Raised when dataset loading or format parsing fails."""
    pass

class LibraryImportError(BenchmarkRunnerException):
    """Raised when candidate package dynamic import fails."""
    pass

class TaskExecutionError(BenchmarkRunnerException):
    """Raised when workload task execution throws an unhandled exception."""
    pass

class EnvironmentValidationError(BenchmarkRunnerException):
    """Raised when host testbed environment checks fail."""
    pass
