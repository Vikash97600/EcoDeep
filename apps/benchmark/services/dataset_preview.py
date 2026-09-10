import csv
import json
import os

class DatasetPreviewService:
    """Provides memory-efficient head previews and full dataset viewing capabilities."""

    @staticmethod
    def preview_file(file_path, dataset_type, max_lines=20):
        if not os.path.exists(file_path):
            return {
                "lines": ["Error: File not found on disk."],
                "is_table": False,
                "headers": [],
                "rows": [],
                "total_lines": 0,
                "is_truncated": False
            }

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if dataset_type == 'CSV':
                    reader = csv.reader(f)
                    all_rows = list(reader)
                    total_lines = len(all_rows)
                    if not all_rows:
                        return {
                            "lines": ["Empty CSV file."],
                            "is_table": True,
                            "headers": [],
                            "rows": [],
                            "total_lines": 0,
                            "is_truncated": False
                        }
                    headers = all_rows[0]
                    data_rows = all_rows[1:]
                    
                    is_truncated = False
                    if max_lines and len(data_rows) > max_lines:
                        rendered_rows = data_rows[:max_lines]
                        is_truncated = True
                    else:
                        rendered_rows = data_rows
                    
                    lines = [", ".join(row) for row in ([headers] + rendered_rows)]
                    return {
                        "lines": lines,
                        "is_table": True,
                        "headers": headers,
                        "rows": rendered_rows,
                        "total_lines": len(data_rows),
                        "is_truncated": is_truncated
                    }

                elif dataset_type == 'JSON':
                    content = f.read()
                    try:
                        parsed = json.loads(content)
                        formatted = json.dumps(parsed, indent=2)
                        all_lines = formatted.splitlines()
                    except Exception:
                        all_lines = content.splitlines()

                    total_lines = len(all_lines)
                    is_truncated = False
                    if max_lines and len(all_lines) > max_lines:
                        lines = all_lines[:max_lines]
                        is_truncated = True
                    else:
                        lines = all_lines

                    return {
                        "lines": lines,
                        "is_table": False,
                        "headers": [],
                        "rows": [],
                        "total_lines": total_lines,
                        "is_truncated": is_truncated
                    }

                else:
                    all_lines = [line.rstrip('\r\n') for line in f]
                    total_lines = len(all_lines)
                    is_truncated = False
                    if max_lines and len(all_lines) > max_lines:
                        lines = all_lines[:max_lines]
                        is_truncated = True
                    else:
                        lines = all_lines

                    return {
                        "lines": lines,
                        "is_table": False,
                        "headers": [],
                        "rows": [],
                        "total_lines": total_lines,
                        "is_truncated": is_truncated
                    }

        except Exception as e:
            return {
                "lines": [f"Preview error: {str(e)}"],
                "is_table": False,
                "headers": [],
                "rows": [],
                "total_lines": 0,
                "is_truncated": False
            }

