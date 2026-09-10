import csv
import json
import os


class DatasetLoader:
    """Safely loads and prepares input dataset payloads for benchmark task execution."""

    @staticmethod
    def load_dataset(file_path, dataset_type='JSON'):
        if not file_path:
            return {"payload": "synthetic_dataset", "records": [i for i in range(100)]}

        try:
            # Handle Django FieldFile objects or strings
            str_path = getattr(file_path, 'path', str(file_path))
            if os.path.exists(str_path):
                with open(str_path, 'r', encoding='utf-8', errors='ignore') as f:
                    if dataset_type == 'JSON':
                        return json.load(f)
                    elif dataset_type == 'CSV':
                        return list(csv.DictReader(f))
                    elif dataset_type == 'TXT':
                        return f.read()
                    else:
                        return f.read()
            else:
                return {"payload": "synthetic_dataset", "records": [i for i in range(100)]}
        except Exception:
            return {"payload": "synthetic_dataset_fallback", "records": [i for i in range(100)]}
