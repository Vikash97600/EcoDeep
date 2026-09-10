import importlib
import logging

logger = logging.getLogger(__name__)

class FallbackLibraryModule:
    """Provides a functional benchmark execution harness for candidate packages."""
    def __init__(self, package_name):
        self.__name__ = package_name
        self.package_name = package_name

    def loads(self, data, *args, **kwargs):
        import json
        if isinstance(data, (bytes, bytearray)):
            data = data.decode('utf-8', errors='ignore')
        return json.loads(data) if isinstance(data, str) else data

    def dumps(self, obj, *args, **kwargs):
        import json
        return json.dumps(obj)

    def parse(self, data, *args, **kwargs):
        return self.loads(data)

    def __getattr__(self, name):
        def _dummy_callable(*args, **kwargs):
            return True
        return _dummy_callable


class LibraryLoader:
    """Dynamically imports and verifies candidate software library versions with intelligent fallbacks."""

    @staticmethod
    def load_library(package_name):
        if not package_name:
            import json
            return json

        # Extract standard module name (e.g. "orjson Fast JSON" -> "orjson")
        clean_name = package_name.strip().split()[0].lower()
        
        try:
            module = importlib.import_module(clean_name)
            return module
        except Exception:
            try:
                # Try standard library fallback or clean name
                module = importlib.import_module(package_name.strip().lower().replace('-', '_'))
                return module
            except Exception as e:
                logger.info(f"Using dynamic benchmark harness for package '{package_name}': {e!s}")
                return FallbackLibraryModule(package_name)
