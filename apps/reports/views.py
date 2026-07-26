from django.shortcuts import render
from django.views import View
from apps.reports.services.report_service import ReportService

class ReportsCenterView(View):
    template_name = 'reports/reports_center.html'

    def get(self, request):
        return render(request, self.template_name)


class ReportExportView(View):
    def get(self, request, report_type='research', format_type='csv'):
        return ReportService.generate_csv_report()
