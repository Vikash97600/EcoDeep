import hashlib

from django.core.exceptions import ValidationError


def validate_dataset_file_extension(value):
    """Validates that uploaded dataset files possess supported extensions."""
    ext = value.name.split('.')[-1].lower()
    valid_extensions = ['json', 'csv', 'xml', 'txt', 'jpg', 'jpeg', 'png', 'parquet']
    if ext not in valid_extensions:
        raise ValidationError(f"Unsupported dataset format '{ext}'. Allowed formats: {', '.join(valid_extensions)}")

def calculate_sha256(file_obj):
    """Calculates SHA256 checksum hash for a file stream."""
    sha256_hash = hashlib.sha256()
    for chunk in file_obj.chunks():
        sha256_hash.update(chunk)
    return sha256_hash.hexdigest()
