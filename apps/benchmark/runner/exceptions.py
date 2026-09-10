class BenchmarkRunnerException(Exception):
    """Base exception for all Benchmark Runner execution failures."""

class DatasetLoadError(BenchmarkRunnerException):
    """Raised when dataset loading or format parsing fails."""

class LibraryImportError(BenchmarkRunnerException):
    """Raised when candidate package dynamic import fails."""

class TaskExecutionError(BenchmarkRunnerException):
    """Raised when workload task execution throws an unhandled exception."""

class EnvironmentValidationError(BenchmarkRunnerException):
    """Raised when host testbed environment checks fail."""
