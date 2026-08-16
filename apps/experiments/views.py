import csv
import io
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from apps.authentication.decorators import researcher_required
from apps.experiments.models import ScientificExperiment, ScientificDataset, DatasetObservation
from apps.experiments.forms import ScientificExperimentForm
from apps.experiments.services.experiment_service import ExperimentService
from apps.experiments.services.report_generator_service import ReportGeneratorService

class ExperimentListView(ListView):
    model = ScientificExperiment
    template_name = 'experiments/experiment_list.html'
    context_object_name = 'experiments'


class ExperimentDetailView(DetailView):
    model = ScientificExperiment
    template_name = 'experiments/experiment_detail.html'
    context_object_name = 'experiment'


@method_decorator(researcher_required, name='dispatch')
class ExperimentCreateView(CreateView):
    model = ScientificExperiment
    form_class = ScientificExperimentForm
    template_name = 'experiments/experiment_form.html'
    success_url = reverse_lazy('experiments:experiment_list')

    def form_valid(self, form):
        form.instance.researcher = self.request.user
        messages.success(self.request, "Scientific experiment created successfully.")
        return super().form_valid(form)


@method_decorator(researcher_required, name='dispatch')
class ExperimentExecuteView(View):
    def post(self, request, pk):
        experiment = get_object_or_404(ScientificExperiment, pk=pk)
        try:
            dataset = ExperimentService.execute_scientific_experiment(experiment)
            messages.success(request, f"Experiment '{experiment.title}' executed successfully! Published Dataset v{dataset.semantic_version}.")
            return redirect('experiments:dataset_detail', pk=dataset.pk)
        except Exception as e:
            messages.error(request, f"Experiment execution failed: {str(e)}")
            return redirect('experiments:experiment_detail', pk=pk)


class DatasetCatalogView(ListView):
    model = ScientificDataset
    template_name = 'experiments/dataset_catalog.html'
    context_object_name = 'datasets'


class DatasetDetailView(DetailView):
    model = ScientificDataset
    template_name = 'experiments/dataset_detail.html'
    context_object_name = 'dataset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latex_table'] = ReportGeneratorService.generate_latex_table(self.object)
        context['markdown_report'] = ReportGeneratorService.generate_markdown_report(self.object)
        return context


class DatasetExportView(View):
    def get(self, request, pk, export_format):
        dataset = get_object_or_404(ScientificDataset, pk=pk)

        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{dataset.dataset_name}_v{dataset.semantic_version}.csv"'

            writer = csv.writer(response)
            writer.writerow([
                'library', 'iteration', 'is_warmup', 'is_outlier',
                'execution_time_ms', 'cpu_utilization_pct', 'ram_rss_mb',
                'energy_joules', 'co2_emissions_g', 'power_watts'
            ])

            for obs in dataset.observations.all():
                writer.writerow([
                    obs.library.library_name, obs.iteration_number, obs.is_warmup, obs.is_outlier,
                    obs.execution_time_ms, obs.cpu_utilization_pct, obs.ram_rss_mb,
                    obs.energy_joules, obs.co2_emissions_g, obs.power_watts
                ])
            return response

        elif export_format == 'json':
            data = {
                'dataset_name': dataset.dataset_name,
                'version': dataset.semantic_version,
                'confidence_index': dataset.confidence_index,
                'data_quality_score': dataset.data_quality_score,
                'checksum_sha256': dataset.checksum_sha256,
                'observations': list(dataset.observations.values(
                    'library__library_name', 'iteration_number', 'is_warmup', 'is_outlier',
                    'execution_time_ms', 'cpu_utilization_pct', 'ram_rss_mb',
                    'energy_joules', 'co2_emissions_g', 'power_watts'
                ))
            }
            return JsonResponse(data, safe=False, json_dumps_params={'indent': 2})

        elif export_format == 'latex':
            latex_code = ReportGeneratorService.generate_latex_table(dataset)
            response = HttpResponse(latex_code, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="{dataset.dataset_name}_table.tex"'
            return response

        return HttpResponse("Unsupported export format", status=400)


class StatisticalReportView(DetailView):
    model = ScientificDataset
    template_name = 'experiments/statistical_report.html'
    context_object_name = 'dataset'
