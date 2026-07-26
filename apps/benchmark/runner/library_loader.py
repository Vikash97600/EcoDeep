import importlib
from apps.benchmark.runner.exceptions import LibraryImportError

class LibraryLoader:
    """Dynamically imports and verifies candidate software library versions."""

    @staticmethod
    def load_library(package_name):
        try:
            module = importlib.import_module(package_name)
            return module
        except ImportError as e:
            raise LibraryImportError(f"Candidate package '{package_name}' could not be imported: {str(e)}")
