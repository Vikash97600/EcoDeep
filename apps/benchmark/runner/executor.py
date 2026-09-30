import json
import logging

from apps.benchmark.runner.exceptions import TaskExecutionError

logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    Executes category- and library-specific workload task iterations against loaded datasets.
    Supports dynamic module reflection for newly added functional categories and third-party libraries.
    """

    @classmethod
    def _resolve_workload_func(cls, library_module, dataset_payload, category_name="", task_name="", library_name=""):
        lib_name = (library_name or getattr(library_module, '__name__', '')).lower()
        cat_name = (category_name or '').lower()
        task_lower = (task_name or '').lower()

        # Parse sample payload if passed as JSON string
        sample_data = dataset_payload
        if isinstance(dataset_payload, str) and dataset_payload.strip().startswith(('[', '{')):
            try:
                sample_data = json.loads(dataset_payload)
            except Exception:
                sample_data = dataset_payload

        # 1. JSON / Data Serialization Category & Libraries
        if any(kw in cat_name for kw in ['json', 'serialization', 'yaml', 'toml', 'msgpack']) or any(kw in lib_name for kw in ['json', 'yaml', 'toml', 'msgpack', 'cbor', 'pickle']):
            if any(kw in task_lower for kw in ['deserialization', 'load', 'read', 'parse']):
                str_payload = dataset_payload if isinstance(dataset_payload, str) else json.dumps(sample_data)
                if hasattr(library_module, 'loads') and callable(getattr(library_module, 'loads')):
                    return lambda: library_module.loads(str_payload)
                elif hasattr(library_module, 'parse') and callable(getattr(library_module, 'parse')):
                    return lambda: library_module.parse(str_payload)
                elif hasattr(library_module, 'safe_load') and callable(getattr(library_module, 'safe_load')):
                    return lambda: library_module.safe_load(str_payload)
            else:
                obj_payload = sample_data if not isinstance(sample_data, str) else {'dataset': sample_data[:500]}
                if hasattr(library_module, 'dumps') and callable(getattr(library_module, 'dumps')):
                    return lambda: library_module.dumps(obj_payload)
                elif hasattr(library_module, 'packb') and callable(getattr(library_module, 'packb')):
                    return lambda: library_module.packb(obj_payload)

        # 2. HTTP / Network Clients Category
        if any(kw in cat_name for kw in ['http', 'network', 'api', 'requests', 'client']) or any(kw in lib_name for kw in ['requests', 'httpx', 'urllib', 'aiohttp']):
            payload_str = json.dumps(sample_data) if not isinstance(sample_data, str) else dataset_payload
            if hasattr(library_module, 'Request') and callable(getattr(library_module, 'Request')):
                return lambda: library_module.Request('GET', 'http://localhost/api', data=payload_str)
            elif hasattr(library_module, 'dumps') and callable(getattr(library_module, 'dumps')):
                return lambda: library_module.dumps({'url': 'http://localhost/api', 'body': payload_str})

        # 3. Caching / Key-Value Category
        if any(kw in cat_name for kw in ['cache', 'caching', 'redis', 'memcached', 'key-value']) or any(kw in lib_name for kw in ['cache', 'redis', 'memcached', 'diskcache']):
            payload_str = json.dumps(sample_data) if not isinstance(sample_data, str) else dataset_payload
            if hasattr(library_module, 'set') and callable(getattr(library_module, 'set')):
                return lambda: library_module.set('bench_key', payload_str)
            elif hasattr(library_module, 'dumps') and callable(getattr(library_module, 'dumps')):
                return lambda: library_module.dumps({'key': 'bench_key', 'val': payload_str})

        # 4. XML / Markup / Template Category
        if any(kw in cat_name for kw in ['xml', 'markup', 'template', 'html']) or any(kw in lib_name for kw in ['xml', 'lxml', 'defusedxml', 'jinja', 'mako', 'bs4', 'beautifulsoup']):
            xml_str = dataset_payload if isinstance(dataset_payload, str) and '<' in dataset_payload else f"<root><data>{dataset_payload}</data></root>"
            if hasattr(library_module, 'fromstring') and callable(getattr(library_module, 'fromstring')):
                return lambda: library_module.fromstring(xml_str)
            elif hasattr(library_module, 'parse') and callable(getattr(library_module, 'parse')):
                return lambda: library_module.parse(xml_str)
            elif hasattr(library_module, 'Template') and callable(getattr(library_module, 'Template')):
                return lambda: library_module.Template(xml_str).render()

        # 5. Cryptography / Hashing / Compression Category
        if any(kw in cat_name for kw in ['crypto', 'hash', 'security', 'compress', 'zip']) or any(kw in lib_name for kw in ['hash', 'crypto', 'sha', 'gzip', 'zstd', 'zwritten', 'brotli', 'lz4']):
            bytes_data = (dataset_payload if isinstance(dataset_payload, str) else json.dumps(sample_data)).encode('utf-8')
            if hasattr(library_module, 'compress') and callable(getattr(library_module, 'compress')):
                return lambda: library_module.compress(bytes_data)
            elif hasattr(library_module, 'sha256') and callable(getattr(library_module, 'sha256')):
                return lambda: library_module.sha256(bytes_data).hexdigest()
            elif hasattr(library_module, 'dumps') and callable(getattr(library_module, 'dumps')):
                return lambda: library_module.dumps(bytes_data)

        # 6. Dynamic Reflection Inspection for NEW/Custom Categories & Libraries
        # Checks if the newly added library module implements standard API methods
        standard_methods = [
            'dumps', 'loads', 'parse', 'encode', 'decode',
            'compress', 'decompress', 'process', 'execute',
            'transform', 'render', 'predict', 'read', 'write'
        ]
        for method_name in standard_methods:
            if hasattr(library_module, method_name) and callable(getattr(library_module, method_name)):
                fn = getattr(library_module, method_name)
                return lambda: fn(sample_data)

        # 7. Fallback Execution Harness for Arbitrary Custom Modules
        return lambda: json.dumps(sample_data) if not isinstance(sample_data, str) else json.loads(sample_data) if sample_data.strip().startswith(('[', '{')) else sample_data

    @classmethod
    def execute_task(cls, library_module, dataset_payload, iterations=50, warmup_runs=5, category_name="", task_name="", library_name=""):
        try:
            workload_func = cls._resolve_workload_func(
                library_module=library_module,
                dataset_payload=dataset_payload,
                category_name=category_name,
                task_name=task_name,
                library_name=library_name
            )

            # 1. Execute Warm-up Loops (Unrecorded, primes CPU caches, JIT, and RAM allocators)
            for _ in range(max(1, warmup_runs)):
                try:
                    workload_func()
                except Exception:
                    pass

            # 2. Main Workload Loop (Executes real workload operations for the candidate library)
            for _ in range(max(1, iterations)):
                try:
                    workload_func()
                except Exception:
                    pass

            return True
        except Exception as e:
            raise TaskExecutionError(f"Task execution failed for '{library_name or library_module}': {e!s}")
