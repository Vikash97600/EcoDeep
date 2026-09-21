import csv
import json
import random
import xml.etree.ElementTree as ET
from io import StringIO
from xml.dom import minidom


class DeterministicDatasetGenerator:
    """
    Generates synthetic, domain-tailored datasets (JSON, CSV, XML, TXT)
    customized according to the functional category and target library.
    """

    @staticmethod
    def _compute_effective_seed(seed, category_name="", library_name="", dataset_name=""):
        eff_seed = int(seed)
        if category_name:
            eff_seed += sum(ord(c) * (i + 1) for i, c in enumerate(category_name)) * 109
        if library_name:
            eff_seed += sum(ord(c) * (i + 1) for i, c in enumerate(library_name)) * 1009
        if dataset_name:
            eff_seed += sum(ord(c) * (i + 1) for i, c in enumerate(dataset_name)) * 37
        return eff_seed % (2**31 - 1)

    @classmethod
    def generate_records(cls, record_count=1000, seed=42, category_name="", library_name="", dataset_name=""):
        eff_seed = cls._compute_effective_seed(seed, category_name, library_name, dataset_name)
        random.seed(eff_seed)

        cat_lower = category_name.lower() if category_name else ""
        records = []

        # Domain 1: Data Serialization / JSON / YAML / TOML
        if any(kw in cat_lower for kw in ['json', 'serialization', 'yaml', 'toml', 'pickle', 'msgpack', 'cbor']):
            domains = ['checkout', 'payment', 'inventory', 'auth', 'analytics']
            statuses = ['SUCCESS', 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']
            for i in range(1, record_count + 1):
                records.append({
                    'transaction_id': f"TXN-{eff_seed % 1000:03d}-{i:06d}",
                    'category': category_name or 'Serialization',
                    'library': library_name or 'Default',
                    'user_id': random.randint(1000, 99999),
                    'service': random.choice(domains),
                    'payload_bytes': random.randint(128, 65536),
                    'execution_time_ms': round(random.uniform(0.1, 45.0), 3),
                    'status': random.choice(statuses),
                    'is_validated': random.choice([True, False]),
                    'metadata': {
                        'client_version': f"v{random.randint(1,5)}.{random.randint(0,9)}",
                        'retry_count': random.randint(0, 3),
                        'confidence_score': round(random.uniform(0.70, 0.99), 4)
                    }
                })

        # Domain 2: HTTP / Networking / REST API
        elif any(kw in cat_lower for kw in ['http', 'network', 'api', 'web', 'rest', 'requests', 'urllib', 'aiohttp', 'httpx']):
            methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
            endpoints = ['/api/v1/users', '/api/v1/products', '/api/v2/telemetry', '/healthz', '/auth/login']
            status_codes = [200, 201, 204, 400, 401, 403, 404, 500, 502]
            for i in range(1, record_count + 1):
                records.append({
                    'request_id': f"REQ-{i:07d}",
                    'method': random.choice(methods),
                    'endpoint': random.choice(endpoints),
                    'status_code': random.choice(status_codes),
                    'latency_ms': round(random.uniform(2.5, 450.0), 2),
                    'request_bytes': random.randint(64, 8192),
                    'response_bytes': random.randint(256, 524288),
                    'client_ip': f"{random.randint(10,192)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                    'keep_alive': random.choice([True, False])
                })

        # Domain 3: Database / ORM
        elif any(kw in cat_lower for kw in ['db', 'database', 'orm', 'sql', 'postgres', 'mysql', 'sqlite']):
            tables = ['users', 'orders', 'audit_logs', 'products', 'sessions']
            for i in range(1, record_count + 1):
                records.append({
                    'query_id': i,
                    'table_name': random.choice(tables),
                    'rows_affected': random.randint(1, 5000),
                    'execution_time_ms': round(random.uniform(0.5, 120.0), 3),
                    'memory_peak_mb': round(random.uniform(4.0, 64.0), 2),
                    'is_cached': random.choice([True, False]),
                    'transaction_active': random.choice([True, False]),
                    'query_hash': f"sha256-{hex(eff_seed + i)[2:]}"
                })

        # Domain 4: Logging / Telemetry
        elif any(kw in cat_lower for kw in ['log', 'logging', 'telemetry', 'trace']):
            levels = ['INFO', 'DEBUG', 'WARN', 'ERROR', 'CRITICAL']
            modules = ['app.auth', 'app.benchmark', 'app.db', 'app.runner', 'app.api']
            for i in range(1, record_count + 1):
                records.append({
                    'log_sequence': i,
                    'log_level': random.choice(levels),
                    'module': random.choice(modules),
                    'thread_id': random.randint(1000, 9999),
                    'cpu_percent': round(random.uniform(5.0, 95.0), 1),
                    'rss_memory_mb': round(random.uniform(12.0, 128.0), 2),
                    'message': f"Telemetry checkpoint {i} for {category_name or 'logging'} benchmark execution."
                })

        # Domain 5: Cryptography / Security
        elif any(kw in cat_lower for kw in ['crypto', 'security', 'hash', 'encrypt', 'auth']):
            algos = ['SHA256', 'AES-256-GCM', 'RSA-4096', 'HMAC-SHA512', 'Ed25519']
            for i in range(1, record_count + 1):
                records.append({
                    'sample_id': i,
                    'algorithm': random.choice(algos),
                    'key_size_bits': random.choice([256, 512, 2048, 4096]),
                    'digest_hex': f"{hex(eff_seed * i + 0xABCDEF)[2:]:064}"[:64],
                    'encrypt_time_us': round(random.uniform(1.2, 850.0), 2),
                    'is_verified': random.choice([True, False])
                })

        # Domain 6: Default / General Category
        else:
            domain_name = (category_name or dataset_name or "Benchmark").replace(" ", "_")
            for i in range(1, record_count + 1):
                records.append({
                    'id': i,
                    'category': category_name or 'General',
                    'library': library_name or 'Default',
                    'metric_name': f"{domain_name}_metric_{i % 5}",
                    'value': round(random.uniform(1.0, 1000.0), 2),
                    'score': round(random.uniform(10.0, 99.9), 2),
                    'category_rank': random.randint(1, 100),
                    'is_valid': random.choice([True, False])
                })

        return records

    @classmethod
    def generate_json(cls, record_count=10000, seed=42, category_name="", library_name="", dataset_name=""):
        records = cls.generate_records(record_count, seed, category_name, library_name, dataset_name)
        return json.dumps(records, indent=2)

    @classmethod
    def generate_csv(cls, record_count=10000, seed=42, category_name="", library_name="", dataset_name=""):
        records = cls.generate_records(record_count, seed, category_name, library_name, dataset_name)
        output = StringIO()
        if not records:
            return ""

        flat_records = []
        for r in records:
            r_copy = r.copy()
            if 'metadata' in r_copy and isinstance(r_copy['metadata'], dict):
                meta = r_copy.pop('metadata')
                for mk, mv in meta.items():
                    r_copy[f"meta_{mk}"] = mv
            flat_records.append(r_copy)

        headers = list(flat_records[0].keys())
        writer = csv.writer(output)
        writer.writerow(headers)
        for r in flat_records:
            writer.writerow([r[h] for h in headers])
        return output.getvalue()

    @classmethod
    def generate_xml(cls, record_count=10000, seed=42, category_name="", library_name="", dataset_name=""):
        records = cls.generate_records(record_count, seed, category_name, library_name, dataset_name)
        root = ET.Element("dataset", {
            "category": category_name or "General",
            "library": library_name or "Default",
            "count": str(len(records))
        })
        for r in records:
            rec_el = ET.SubElement(root, "record")
            for k, v in r.items():
                if isinstance(v, dict):
                    meta_el = ET.SubElement(rec_el, k)
                    for mk, mv in v.items():
                        sub_el = ET.SubElement(meta_el, mk)
                        sub_el.text = str(mv)
                else:
                    sub_el = ET.SubElement(rec_el, k)
                    sub_el.text = str(v)
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    @classmethod
    def generate_txt(cls, line_count=5000, seed=42, category_name="", library_name="", dataset_name=""):
        eff_seed = cls._compute_effective_seed(seed, category_name, library_name, dataset_name)
        random.seed(eff_seed)

        cat_title = category_name or "Green Software"
        lib_title = library_name or "EcoDep Benchmark Engine"

        vocab = [
            "green_score", "energy_efficiency", "resource_utilization", "execution_time",
            "cpu_cycles", "memory_rss", "co2_emissions", "joules", "carbon_footprint",
            cat_title.lower().replace(" ", "_"), lib_title.lower().replace(" ", "_")
        ]

        lines = [f"# Synthetic Text Payload: {dataset_name or cat_title} ({lib_title})"]
        for i in range(1, line_count + 1):
            sentence = " ".join(random.choices(vocab, k=10))
            lines.append(f"[Line {i:06d}] {sentence}")
        return "\n".join(lines)

    @classmethod
    def generate_dataset(cls, dataset_type='JSON', record_count=10000, seed=42, category_name="", library_name="", dataset_name=""):
        dtype = (dataset_type or 'JSON').upper()
        if dtype == 'JSON':
            return cls.generate_json(record_count, seed, category_name, library_name, dataset_name)
        elif dtype == 'CSV':
            return cls.generate_csv(record_count, seed, category_name, library_name, dataset_name)
        elif dtype == 'XML':
            return cls.generate_xml(record_count, seed, category_name, library_name, dataset_name)
        elif dtype == 'TXT':
            return cls.generate_txt(record_count, seed, category_name, library_name, dataset_name)
        else:
            return cls.generate_json(record_count, seed, category_name, library_name, dataset_name)
