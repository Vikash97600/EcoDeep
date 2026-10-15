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


class CategoryPurgeService:
    """Safely cascades deletion of all libraries, benchmark sessions, tasks,
    datasets, and related artifacts associated with a functional category."""

    @staticmethod
    def get_category_purge_preview(category):
        """Calculates exact counts and items affected prior to deletion for confirmation."""
        from django.db.models import Q
        from apps.benchmark.models import (
            BenchmarkDataset,
            BenchmarkResult,
            BenchmarkSession,
            BenchmarkTask,
        )
        from apps.libraries.models import Library
        from apps.mcdm.models import MCDMEvaluationRun

        libraries = list(Library.objects.filter(category=category).order_by('library_name'))
        tasks = list(BenchmarkTask.objects.filter(category=category).order_by('task_name'))
        datasets = list(BenchmarkDataset.objects.filter(
            Q(dataset_category=category) | Q(tasks__category=category)
        ).distinct().order_by('dataset_name'))

        sessions = list(BenchmarkSession.objects.filter(
            Q(jobs__task__category=category) |
            Q(jobs__library_version__library__category=category) |
            Q(results__task__category=category) |
            Q(results__library_version__library__category=category) |
            Q(results__dataset__in=datasets)
        ).distinct().order_by('-created_at'))

        results_count = BenchmarkResult.objects.filter(
            Q(task__category=category) |
            Q(library_version__library__category=category) |
            Q(session__in=sessions)
        ).distinct().count()

        mcdm_count = MCDMEvaluationRun.objects.filter(category=category).count()

        return {
            'category_id': category.id,
            'category_name': category.category_name,
            'category_slug': category.slug,
            'libraries_count': len(libraries),
            'libraries': [lib.library_name for lib in libraries],
            'sessions_count': len(sessions),
            'sessions': [f"{s.session_name} (#{s.id})" for s in sessions],
            'tasks_count': len(tasks),
            'tasks': [t.task_name for t in tasks],
            'datasets_count': len(datasets),
            'datasets': [f"{d.dataset_name} ({d.dataset_type})" for d in datasets],
            'results_count': results_count,
            'mcdm_count': mcdm_count,
        }

    @staticmethod
    def purge_category_data(category, delete_category=False, user=None, ip_address=None):
        """Executes atomic cascading deletion of libraries, sessions, tasks, datasets, and files."""
        import os
        from django.db import transaction
        from django.db.models import Q
        from apps.benchmark.models import (
            BenchmarkDataset,
            BenchmarkSession,
            BenchmarkTask,
        )
        from apps.core.models import AuditLog
        from apps.knowledge_graph.models import KnowledgeGraphNode
        from apps.libraries.models import Library
        from apps.mcdm.models import MCDMEvaluationRun

        preview = CategoryPurgeService.get_category_purge_preview(category)
        category_name = category.category_name
        category_id = category.id

        libraries = list(Library.objects.filter(category=category))
        lib_ids = [l.id for l in libraries]

        tasks = list(BenchmarkTask.objects.filter(category=category))
        task_ids = [t.id for t in tasks]

        datasets = list(BenchmarkDataset.objects.filter(
            Q(dataset_category=category) | Q(tasks__category=category)
        ).distinct())
        dataset_ids = [d.id for d in datasets]

        # Gather dataset disk files to remove
        dataset_files_to_delete = []
        for d in datasets:
            if d.file_path and hasattr(d.file_path, 'path'):
                try:
                    dataset_files_to_delete.append(d.file_path.path)
                except Exception:
                    pass
            for v in d.versions.all():
                if v.file_path and hasattr(v.file_path, 'path'):
                    try:
                        dataset_files_to_delete.append(v.file_path.path)
                    except Exception:
                        pass

        sessions = list(BenchmarkSession.objects.filter(
            Q(jobs__task__category=category) |
            Q(jobs__library_version__library__category=category) |
            Q(results__task__category=category) |
            Q(results__library_version__library__category=category) |
            Q(results__dataset__in=datasets)
        ).distinct())
        session_ids = [s.id for s in sessions]

        with transaction.atomic():
            # 1. Delete BenchmarkSessions
            if session_ids:
                BenchmarkSession.objects.filter(id__in=session_ids).delete()

            # 2. Delete BenchmarkTasks
            if task_ids:
                BenchmarkTask.objects.filter(id__in=task_ids).delete()

            # 3. Delete Datasets (model records)
            if dataset_ids:
                BenchmarkDataset.objects.filter(id__in=dataset_ids).delete()

            # 4. Clean KnowledgeGraph nodes for the libraries
            if lib_ids:
                KnowledgeGraphNode.objects.filter(node_type='LIBRARY', entity_id__in=lib_ids).delete()

            # 5. Clean MCDMEvaluationRun for this category
            MCDMEvaluationRun.objects.filter(category=category).delete()

            # 6. Delete Libraries (this cascades LibraryVersions, SimilarLibraryMappings, embeddings, predictions, etc.)
            if lib_ids:
                Library.objects.filter(id__in=lib_ids).delete()

            # 7. Optionally delete the Category itself
            if delete_category:
                KnowledgeGraphNode.objects.filter(node_type='CATEGORY', entity_id=category_id).delete()
                category.delete()

            # 8. Record in AuditLog
            AuditLog.objects.create(
                user=user if user and user.is_authenticated else None,
                action='CATEGORY_DATA_PURGED',
                module='libraries',
                description=(
                    f"Purged category '{category_name}': {preview['libraries_count']} libraries, "
                    f"{preview['sessions_count']} benchmark sessions, {preview['tasks_count']} tasks, "
                    f"{preview['datasets_count']} datasets. Category deleted: {delete_category}"
                ),
                ip_address=ip_address
            )

        # 9. Clean up physical files on storage
        deleted_files_count = 0
        for fpath in dataset_files_to_delete:
            if fpath and os.path.isfile(fpath):
                try:
                    os.remove(fpath)
                    deleted_files_count += 1
                except OSError:
                    pass

        return {
            'category_name': category_name,
            'libraries_deleted': preview['libraries_count'],
            'sessions_deleted': preview['sessions_count'],
            'tasks_deleted': preview['tasks_count'],
            'datasets_deleted': preview['datasets_count'],
            'files_deleted': deleted_files_count,
            'results_deleted': preview['results_count'],
            'category_deleted': delete_category,
        }

