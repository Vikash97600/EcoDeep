import csv
import re
from io import StringIO

from django.utils.text import slugify

from apps.libraries.models import (
    Category,
    Library,
    ProgrammingLanguage,
)


class BulkDataService:
    """Handles robust bulk data imports and exports in CSV and JSON formats."""

    @staticmethod
    def _normalize_key(key: str) -> str:
        """Strips special characters and lowercases header names."""
        clean = re.sub(r'[^a-zA-Z0-9]', '', str(key).lower())
        if clean in ['libraryname', 'library', 'name', 'packagename', 'package', 'lib']:
            return 'library_name'
        if clean in ['officialname', 'title', 'officialtitle']:
            return 'official_name'
        if clean in ['language', 'programminglanguage', 'languagename', 'lang']:
            return 'language'
        if clean in ['category', 'categoryname', 'functionalcategory', 'cat']:
            return 'category'
        if clean in ['version', 'currentversion', 'versionnumber', 'ver']:
            return 'current_version'
        if clean in ['description', 'desc', 'summary', 'details']:
            return 'description'
        if clean in ['packagemanager', 'packagemgr', 'manager']:
            return 'package_manager'
        if clean in ['license', 'licensetype']:
            return 'license'
        if clean in ['repositoryurl', 'repository', 'repo', 'github', 'gitlab', 'git']:
            return 'repository_url'
        if clean in ['documentationurl', 'documentation', 'docs']:
            return 'documentation_url'
        if clean in ['homepageurl', 'homepage', 'website', 'url']:
            return 'homepage_url'
        if clean in ['downloads', 'monthlydownloads']:
            return 'downloads'
        if clean in ['popularityscore', 'popularity', 'stars']:
            return 'popularity_score'
        return clean

    @staticmethod
    def import_libraries_csv(file):
        """Imports libraries from a CSV file with automatic header mapping and encoding detection."""
        if hasattr(file, 'read'):
            raw_data = file.read()
            if isinstance(raw_data, bytes):
                try:
                    text_data = raw_data.decode('utf-8-sig')
                except UnicodeDecodeError:
                    text_data = raw_data.decode('latin-1', errors='replace')
            else:
                text_data = str(raw_data)
        else:
            text_data = str(file)

        f = StringIO(text_data)
        reader = csv.reader(f)
        try:
            raw_headers = next(reader)
        except StopIteration:
            return 0

        header_map = [BulkDataService._normalize_key(h) for h in raw_headers]
        created_count = 0
        updated_count = 0

        for row in reader:
            if not row or all(not str(val).strip() for val in row):
                continue

            row_data = {}
            for idx, val in enumerate(row):
                if idx < len(header_map):
                    row_data[header_map[idx]] = str(val).strip()

            lib_name = row_data.get('library_name', '').strip()
            if not lib_name:
                continue

            lang_name = row_data.get('language', 'Python').strip() or 'Python'
            cat_name = row_data.get('category', 'Data Serialization').strip() or 'Data Serialization'
            official_name = row_data.get('official_name', lib_name).strip() or lib_name
            desc = row_data.get('description', f'{official_name} open-source package').strip() or f'{official_name} open-source package'
            version = row_data.get('current_version', '1.0.0').strip() or '1.0.0'
            license_type = row_data.get('license', 'MIT').strip() or 'MIT'
            pkg_mgr = row_data.get('package_manager', 'PyPI').strip() or 'PyPI'
            repo_url = row_data.get('repository_url', '').strip()
            docs_url = row_data.get('documentation_url', '').strip()
            home_url = row_data.get('homepage_url', '').strip()

            downloads = 0
            try:
                downloads = int(row_data.get('downloads', 0))
            except (ValueError, TypeError):
                downloads = 0

            # Get or create language and category
            lang_slug = slugify(lang_name) or 'python'
            lang = ProgrammingLanguage.objects.filter(language_name__iexact=lang_name).first()
            if not lang:
                lang, _ = ProgrammingLanguage.objects.get_or_create(
                    slug=lang_slug,
                    defaults={'language_name': lang_name.capitalize(), 'description': f'{lang_name} programming ecosystem'}
                )

            cat_slug = slugify(cat_name) or 'general'
            cat = Category.objects.filter(category_name__iexact=cat_name).first()
            if not cat:
                cat, _ = Category.objects.get_or_create(
                    slug=cat_slug,
                    defaults={'category_name': cat_name, 'description': f'{cat_name} libraries and modules'}
                )

            existing_lib = Library.objects.filter(library_name__iexact=lib_name, programming_language=lang).first()
            if existing_lib:
                existing_lib.official_name = official_name
                existing_lib.category = cat
                existing_lib.description = desc
                existing_lib.current_version = version
                existing_lib.license = license_type
                if repo_url:
                    existing_lib.repository_url = repo_url
                if docs_url:
                    existing_lib.documentation_url = docs_url
                if home_url:
                    existing_lib.homepage_url = home_url
                if downloads:
                    existing_lib.downloads = downloads
                existing_lib.save()
                updated_count += 1
            else:
                Library.objects.create(
                    library_name=lib_name,
                    official_name=official_name,
                    programming_language=lang,
                    category=cat,
                    description=desc,
                    package_manager=pkg_mgr,
                    current_version=version,
                    license=license_type,
                    repository_url=repo_url,
                    documentation_url=docs_url,
                    homepage_url=home_url,
                    downloads=downloads
                )
                created_count += 1

        return created_count + updated_count

    @staticmethod
    def export_libraries_csv():
        """Generates a CSV string containing all catalog libraries with comprehensive metadata."""
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Library Name', 'Official Name', 'Language', 'Category', 'Version',
            'License', 'Package Manager', 'Description', 'Repository URL',
            'Documentation URL', 'Homepage URL', 'Downloads'
        ])

        libraries = Library.objects.select_related('programming_language', 'category').all()
        for lib in libraries:
            writer.writerow([
                lib.library_name,
                lib.official_name,
                lib.programming_language.language_name if lib.programming_language else 'Python',
                lib.category.category_name if lib.category else 'General',
                lib.current_version,
                lib.license,
                lib.package_manager,
                lib.description,
                lib.repository_url,
                lib.documentation_url,
                lib.homepage_url,
                lib.downloads
            ])

        return output.getvalue()
