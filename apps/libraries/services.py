import csv
import json
from io import StringIO, TextIOWrapper
from django.core.exceptions import ValidationError
from apps.libraries.models import Library, Category, ProgrammingLanguage, SimilarLibraryMapping

class BulkDataService:
    """Handles bulk data imports and exports in CSV and JSON formats."""

    @staticmethod
    def import_libraries_csv(file):
        """Imports libraries from a CSV file."""
        csv_file = TextIOWrapper(file.file, encoding='utf-8')
        reader = csv.DictReader(csv_file)
        created_count = 0
        
        for row in reader:
            lang_name = row.get('language', 'Python').strip()
            cat_name = row.get('category', 'Data Serialization').strip()
            lib_name = row.get('library_name', '').strip()
            official_name = row.get('official_name', lib_name).strip()
            
            if not lib_name:
                continue

            lang, _ = ProgrammingLanguage.objects.get_or_create(language_name=lang_name, defaults={'slug': lang_name.lower()})
            cat, _ = Category.objects.get_or_create(category_name=cat_name, defaults={'slug': cat_name.lower(), 'description': f'{cat_name} packages'})

            lib, created = Library.objects.get_or_create(
                library_name=lib_name,
                programming_language=lang,
                defaults={
                    'official_name': official_name,
                    'category': cat,
                    'description': row.get('description', 'Imported library'),
                    'current_version': row.get('current_version', '1.0.0'),
                    'license': row.get('license', 'MIT')
                }
            )
            if created:
                created_count += 1

        return created_count

    @staticmethod
    def export_libraries_csv():
        """Generates a CSV string containing all catalog libraries."""
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Library Name', 'Official Name', 'Language', 'Category', 'Version', 'License', 'Downloads'])

        for lib in Library.objects.select_related('programming_language', 'category').all():
            writer.writerow([
                lib.id, lib.library_name, lib.official_name,
                lib.programming_language.language_name, lib.category.category_name,
                lib.current_version, lib.license, lib.downloads
            ])

        return output.getvalue()
