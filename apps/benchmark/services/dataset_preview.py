import csv
import json

class DatasetPreviewService:
    """Provides memory-efficient head previews of datasets without loading entire files into RAM."""

    @staticmethod
    def preview_file(file_path, dataset_type, max_lines=20):
        lines = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if dataset_type == 'CSV':
                    reader = csv.reader(f)
                    for index, row in enumerate(reader):
                        if index >= max_lines:
                            break
                        lines.append(row)
                else:
                    for index, line in enumerate(f):
                        if index >= max_lines:
                            break
                        lines.append(line.strip())
        except Exception as e:
            lines = [f"Preview error: {str(e)}"]
        return lines
