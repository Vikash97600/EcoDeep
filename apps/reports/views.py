from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib import messages
from apps.reports.models import (
    AcademicReport, ResearchArtifactPackage, DocumentFormatChoices, PublicationFormatChoices
)
from apps.reports.forms import ThesisGeneratorForm, IEEEPaperGeneratorForm
from apps.reports.services.thesis_generator_service import ThesisGeneratorService
from apps.reports.services.ieee_paper_generator_service import IEEEPaperGeneratorService
from apps.reports.services.artifact_bundle_service import ArtifactBundleService
from apps.reports.services.export_service import ExportService
from apps.reports.services.report_service import ReportService
from apps.libraries.models import Category

class ReportsCenterView(View):
    template_name = 'reports/reports_center.html'

    def get(self, request):
        context = {
            'total_reports': AcademicReport.objects.count(),
            'total_theses': AcademicReport.objects.filter(publication_format=PublicationFormatChoices.MCA_DISSERTATION).count(),
            'total_ieee_papers': AcademicReport.objects.filter(publication_format=PublicationFormatChoices.IEEE_CONFERENCE).count(),
            'recent_reports': AcademicReport.objects.select_related('category').order_by('-created_at')[:8],
            'categories': Category.objects.all()[:5]
        }
        return render(request, self.template_name, context)


class ThesisGeneratorStudioView(View):
    template_name = 'reports/thesis_generator.html'

    def get(self, request):
        form = ThesisGeneratorForm()
        cat_id = request.GET.get('category')
        report = None

        if cat_id:
            category = get_object_or_404(Category, pk=cat_id)
            author = request.GET.get('author_name', 'Vikash Kumar')
            title = request.GET.get('title')
            report = ThesisGeneratorService.generate_dissertation(category, author_name=author, title=title)
            # Auto-generate Open Science artifact package
            ArtifactBundleService.generate_replication_package(report)
            form = ThesisGeneratorForm(initial={'category': category, 'author_name': author, 'title': title})

        context = {
            'form': form,
            'report': report
        }
        return render(request, self.template_name, context)


class IEEEPaperGeneratorStudioView(View):
    template_name = 'reports/ieee_generator.html'

    def get(self, request):
        form = IEEEPaperGeneratorForm()
        cat_id = request.GET.get('category')
        report = None

        if cat_id:
            category = get_object_or_404(Category, pk=cat_id)
            author = request.GET.get('author_name', 'Vikash Kumar')
            title = request.GET.get('title')
            report = IEEEPaperGeneratorService.generate_ieee_paper(category, author_name=author, title=title)
            # Auto-generate Open Science artifact package
            ArtifactBundleService.generate_replication_package(report)
            form = IEEEPaperGeneratorForm(initial={'category': category, 'author_name': author, 'title': title})

        context = {
            'form': form,
            'report': report
        }
        return render(request, self.template_name, context)


class ReportDetailView(DetailView):
    model = AcademicReport
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'


class ArtifactPackageListView(ListView):
    model = ResearchArtifactPackage
    template_name = 'reports/artifact_packages.html'
    context_object_name = 'packages'


class ReportExportDocumentView(View):
    def get(self, request, pk, format_choice):
        report = get_object_or_404(AcademicReport, pk=pk)
        return ExportService.export_document(report, format_choice=format_choice)


class ReportExportView(View):
    def get(self, request, report_type='research', format_type='csv'):
        return ReportService.generate_csv_report()
