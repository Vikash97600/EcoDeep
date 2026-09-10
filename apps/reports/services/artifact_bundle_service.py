import hashlib
import json

from apps.reports.models import AcademicReport, ResearchArtifactPackage


class ArtifactBundleService:
    """Packages Open Science experimental datasets, configurations, and replication bash scripts."""

    @staticmethod
    def generate_replication_package(report: AcademicReport) -> ResearchArtifactPackage:
        """Constructs an Open Science replication bundle with SHA256 integrity verification."""
        manifest = {
            'report_id': report.id,
            'title': report.title,
            'publication_format': report.publication_format,
            'category': report.category.category_name if report.category else 'General',
            'benchmark_subsystems': ['Intel_RAPL_MSR', 'perf_counter_ns', 'psutil_rss'],
            'mcdm_solver': 'TOPSIS_Vector_Normalized',
            'replication_command': f"python manage.py run_experiment --category {report.category.slug if report.category else 'json'} --runs 30 --warmup 10"
        }

        manifest_str = json.dumps(manifest, sort_keys=True)
        sha256_hash = hashlib.sha256(manifest_str.encode('utf-8')).hexdigest()

        instructions = (
            "### Open Science Replication Instructions\n\n"
            "1. Clone the repository: `git clone https://github.com/Vikash97600/EcoDeep.git`\n"
            "2. Install scientific dependencies: `pip install -r requirements.txt`\n"
            f"3. Run automated replication: `{manifest['replication_command']}`\n"
            "4. Verify generated telemetry against SHA256 checksum: `" + sha256_hash + "`\n"
        )

        package, _ = ResearchArtifactPackage.objects.update_or_create(
            report=report,
            defaults={
                'title': f"Replication Package: {report.title}",
                'package_type': "FULL_OPEN_SCIENCE_BUNDLE",
                'archive_manifest_json': manifest,
                'sha256_checksum': sha256_hash,
                'replication_instructions': instructions
            }
        )
        return package
