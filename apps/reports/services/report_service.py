import csv
from django.http import HttpResponse, JsonResponse
from apps.benchmark.models import BenchmarkResult
from apps.recommendation.models import GreenScore

class ReportService:
    """Generates research reports and exports in CSV and JSON formats."""

    @staticmethod
    def generate_csv_report():
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ecodep_research_report.csv"'
        writer = csv.writer(response)

        writer.writerow([
            'Result_ID', 'Package_Version', 'Task_Name', 'Dataset_Name',
            'Execution_Time_MS', 'Peak_RAM_MB', 'Avg_CPU_Pct', 'Energy_Joules',
            'CO2_Grams', 'Green_Score'
        ])

        results = BenchmarkResult.objects.select_related(
            'library_version__library', 'task', 'dataset'
        ).order_by('-created_at')

        for r in results:
            writer.writerow([
                r.id, str(r.library_version), r.task.task_name, r.dataset.dataset_name,
                r.execution_time, r.peak_memory, r.average_cpu, r.energy, r.co2, r.green_score
            ])

        return response
