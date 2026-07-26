import csv
from django.http import HttpResponse, JsonResponse
from apps.benchmark.models import BenchmarkResult

class ExportService:
    """Exports benchmark repository data to CSV or JSON formats."""

    @staticmethod
    def export_repository_csv(queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ecodep_benchmark_repository.csv"'
        writer = csv.writer(response)

        writer.writerow([
            'Result_ID', 'Session_ID', 'Package_Version', 'Category', 'Task_Name',
            'Dataset_Name', 'Execution_Time_MS', 'Average_CPU_Pct', 'Peak_Memory_MB',
            'Energy_Joules', 'CO2_Grams', 'Green_Score'
        ])

        for r in queryset:
            writer.writerow([
                r.id, r.session.id, str(r.library_version), r.task.category.category_name,
                r.task.task_name, r.dataset.dataset_name, r.execution_time, r.average_cpu,
                r.peak_memory, r.energy, r.co2, r.green_score
            ])

        return response
