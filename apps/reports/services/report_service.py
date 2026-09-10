import csv

from django.http import HttpResponse

from apps.libraries.models import Library


class ReportService:
    """Orchestrates academic report compilation and CSV data exporting."""

    @staticmethod
    def generate_csv_report() -> HttpResponse:
        """Generates a downloadable CSV export of all candidate libraries and green telemetry."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ecodep_benchmark_dataset.csv"'

        writer = csv.writer(response)
        writer.writerow(['Library Name', 'Category', 'Version', 'Language', 'Created At'])

        for lib in Library.objects.select_related('category', 'programming_language').all():
            writer.writerow([
                lib.library_name,
                lib.category.category_name if lib.category else 'N/A',
                lib.current_version,
                lib.programming_language.language_name if lib.programming_language else 'N/A',
                lib.created_at.strftime('%Y-%m-%d')
            ])

        return response
