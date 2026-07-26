import json
import csv
import random
from io import StringIO

class DeterministicDatasetGenerator:
    """Generates synthetic JSON, CSV, XML, and TXT datasets using fixed pseudo-random seeds."""

    @staticmethod
    def generate_json(record_count=10000, seed=42):
        random.seed(seed)
        records = []
        for i in range(1, record_count + 1):
            records.append({
                'id': i,
                'uuid': f"user-{i:06d}",
                'name': f"Person_{i}",
                'email': f"user{i}@ecodep.local",
                'age': random.randint(18, 70),
                'score': round(random.uniform(10.0, 99.9), 2),
                'is_active': random.choice([True, False])
            })
        return json.dumps(records, indent=2)

    @staticmethod
    def generate_csv(record_count=10000, seed=42):
        random.seed(seed)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['id', 'uuid', 'name', 'email', 'age', 'score', 'is_active'])
        for i in range(1, record_count + 1):
            writer.writerow([
                i, f"user-{i:06d}", f"Person_{i}", f"user{i}@ecodep.local",
                random.randint(18, 70), round(random.uniform(10.0, 99.9), 2),
                random.choice([True, False])
            ])
        return output.getvalue()

    @staticmethod
    def generate_txt(line_count=5000, seed=42):
        random.seed(seed)
        words = ["energy", "green", "software", "benchmark", "dependency", "python", "optimization", "joules"]
        lines = []
        for i in range(1, line_count + 1):
            sentence = " ".join(random.choices(words, k=10))
            lines.append(f"Line {i}: {sentence}")
        return "\n".join(lines)
