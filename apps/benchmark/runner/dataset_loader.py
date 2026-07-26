import json
import csv
from apps.benchmark.runner.exceptions import DatasetLoadError

class DatasetLoader:
    """Safely loads and prepares input dataset payloads for benchmark task execution."""

    @staticmethod
    def load_dataset(file_path, dataset_type):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if dataset_type == 'JSON':
                    return json.load(f)
                elif dataset_type == 'CSV':
                    return list(csv.DictReader(f))
                elif dataset_type == 'TXT':
                    return f.read()
                else:
                    return f.read()
        except Exception as e:
            raise DatasetLoadError(f"Failed to load dataset at '{file_path}': {str(e)}")
