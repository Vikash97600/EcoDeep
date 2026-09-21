import csv
import os

from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from apps.authentication.decorators import admin_required, researcher_required
from apps.benchmark.forms import (
    BenchmarkDatasetForm,
    BenchmarkSessionForm,
    BenchmarkTaskForm,
    DatasetGeneratorForm,
)
from apps.benchmark.models import (
    BenchmarkDataset,
    BenchmarkJob,
    BenchmarkProfile,
    BenchmarkResult,
    BenchmarkSession,
    BenchmarkTask,
    DatasetVersion,
    RawExecutionSample,
    WorkerNode,
)
from apps.benchmark.runner.runner import BenchmarkRunner
from apps.benchmark.services.comparison_service import ComparisonService
from apps.benchmark.services.dataset_generator import DeterministicDatasetGenerator
from apps.benchmark.services.dataset_preview import DatasetPreviewService
from apps.benchmark.services.environment_service import EnvironmentService
from apps.benchmark.services.export_service import ExportService
from apps.benchmark.services.orchestrator.execution_monitor_service import (
    ExecutionMonitorService,
)
from apps.benchmark.services.orchestrator.scheduler_service import SchedulerService
from apps.benchmark.services.repository_service import RepositoryService
from apps.benchmark.services.session_service import SessionService
from apps.benchmark.services.statistics_service import StatisticalAnalysisService
from apps.benchmark.validators import calculate_sha256
from apps.core.models import AuditLog


class BenchmarkDashboardView(View):
    template_name = 'benchmark/dashboard.html'

    def get(self, request):
        is_valid_env, env_details = EnvironmentService.validate_environment()
        context = {
            'host_env': EnvironmentService.get_host_environment(),
            'env_details': env_details,
            'is_valid_env': is_valid_env,
            'total_sessions': BenchmarkSession.objects.count(),
            'total_tasks': BenchmarkTask.objects.count(),
            'total_datasets': BenchmarkDataset.objects.count(),
            'pending_jobs': BenchmarkJob.objects.filter(status='PENDING').count(),
            'recent_sessions': BenchmarkSession.objects.select_related('admin').order_by('-start_time')[:5],
        }
        return render(request, self.template_name, context)


class SessionListView(ListView):
    model = BenchmarkSession
    template_name = 'benchmark/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 10


class SessionDetailView(DetailView):
    model = BenchmarkSession
    template_name = 'benchmark/session_detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jobs'] = self.object.jobs.select_related('library_version__library', 'task').all()
        context['results'] = self.object.results.select_related('library_version__library', 'task').all()
        return context


@method_decorator(researcher_required, name='dispatch')
class SessionCreateView(View):
    template_name = 'benchmark/session_form.html'

    def get(self, request):
        form = BenchmarkSessionForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = BenchmarkSessionForm(request.POST)
        if form.is_valid():
            session = SessionService.create_session(
                session_name=form.cleaned_data['session_name'],
                admin_user=request.user,
                task=form.cleaned_data['task'],
                library_versions=form.cleaned_data['library_versions'],
                notes=form.cleaned_data.get('notes', '')
            )
            
            AuditLog.objects.create(
                user=request.user,
                action='BENCHMARK_SESSION_CREATED',
                module='benchmark',
                description=f"Created session #{session.id} ({session.session_name})",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Benchmark Session #{session.id} created and queued successfully.")
            return redirect('benchmark:session_detail', pk=session.id)

        return render(request, self.template_name, {'form': form})


@method_decorator(admin_required, name='dispatch')
class SessionCancelView(View):
    def post(self, request, pk):
        SessionService.cancel_session(pk, request.user)
        messages.warning(request, f"Benchmark Session #{pk} has been cancelled.")
        return redirect('benchmark:session_detail', pk=pk)


class JobQueueListView(ListView):
    model = BenchmarkJob
    template_name = 'benchmark/job_queue.html'
    context_object_name = 'jobs'
    paginate_by = 15

    def get_queryset(self):
        return BenchmarkJob.objects.select_related('session', 'library_version__library', 'task').order_by('status', '-priority')


# --- ORCHESTRATION & WORKER VIEWS ---

class OrchestratorDashboardView(View):
    template_name = 'benchmark/orchestrator_dashboard.html'

    def get(self, request):
        summary = ExecutionMonitorService.get_orchestrator_summary()
        return render(request, self.template_name, {'summary': summary})


class WorkerNodeListView(ListView):
    model = WorkerNode
    template_name = 'benchmark/worker_nodes.html'
    context_object_name = 'workers'


@method_decorator(researcher_required, name='dispatch')
class DispatchJobView(View):
    def post(self, request):
        success, message = SchedulerService.dispatch_next_job()
        if success:
            messages.success(request, message)
        else:
            messages.warning(request, message)
        return redirect('benchmark:orchestrator_dashboard')


# --- RESEARCH REPOSITORY VIEWS ---

class RepositoryListView(ListView):
    model = BenchmarkResult
    template_name = 'benchmark/repository.html'
    context_object_name = 'results'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q')
        cat_id = self.request.GET.get('category')
        task_id = self.request.GET.get('task')
        return RepositoryService.filter_repository(category_id=cat_id, task_id=task_id, search_query=query)


class RepositoryDetailView(DetailView):
    model = BenchmarkResult
    template_name = 'benchmark/result_detail.html'
    context_object_name = 'result'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['raw_time_count'] = self.object.raw_samples.count()
        context['raw_cpu_count'] = self.object.cpu_samples.count()
        context['raw_memory_count'] = self.object.memory_samples.count()
        return context


class CompareResultsView(View):
    template_name = 'benchmark/compare_results.html'

    def get(self, request):
        result_ids = request.GET.getlist('ids')
        comparison_data = {}
        if result_ids:
            comparison_data = ComparisonService.compare_results(result_ids)
        return render(request, self.template_name, {'comparison': comparison_data})


class RepositoryExportView(View):
    def get(self, request, format_type='csv'):
        queryset = RepositoryService.filter_repository()
        return ExportService.export_repository_csv(queryset)


# --- RUNNER & MEASUREMENT VIEWS ---

class RunnerDashboardView(View):
    template_name = 'benchmark/runner_dashboard.html'

    def get(self, request):
        context = {
            'running_jobs': BenchmarkJob.objects.filter(status='RUNNING').select_related('session', 'library_version__library', 'task'),
            'pending_jobs': BenchmarkJob.objects.filter(status='PENDING').select_related('session', 'library_version__library', 'task'),
            'completed_jobs': BenchmarkJob.objects.filter(status='COMPLETED').select_related('session', 'library_version__library', 'task')[:10],
            'failed_jobs': BenchmarkJob.objects.filter(status='FAILED').select_related('session', 'library_version__library', 'task')[:10],
        }
        return render(request, self.template_name, context)


@method_decorator(researcher_required, name='dispatch')
class TriggerRunnerView(View):
    def post(self, request, session_id):
        runner = BenchmarkRunner(session_id=session_id)
        runner.run()
        messages.success(request, f"Benchmark Runner completed execution for Session #{session_id}!")
        return redirect('benchmark:session_detail', pk=session_id)


class JobDetailView(DetailView):
    model = BenchmarkJob
    template_name = 'benchmark/job_details.html'
    context_object_name = 'job'


class TimeMonitorView(View):
    template_name = 'benchmark/time_monitor.html'

    def get(self, request, result_id):
        result = get_object_or_404(BenchmarkResult, pk=result_id)
        samples = [s.elapsed_nanoseconds for s in result.raw_samples.all()]
        stats = StatisticalAnalysisService.calculate_statistics(samples)
        return render(request, self.template_name, {'result': result, 'stats': stats})


class TimeSamplesView(ListView):
    model = RawExecutionSample
    template_name = 'benchmark/time_samples.html'
    context_object_name = 'samples'
    paginate_by = 25

    def get_queryset(self):
        return RawExecutionSample.objects.filter(result_id=self.kwargs['result_id']).order_by('iteration_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['result'] = get_object_or_404(BenchmarkResult, pk=self.kwargs['result_id'])
        return context


class TimeExportView(View):
    def get(self, request, result_id, format_type='csv'):
        result = get_object_or_404(BenchmarkResult, pk=result_id)
        samples = result.raw_samples.all()

        if format_type == 'json':
            data = [
                {'iteration': s.iteration_number, 'elapsed_ns': s.elapsed_nanoseconds, 'elapsed_ms': s.elapsed_nanoseconds / 1e6, 'is_outlier': s.is_outlier}
                for s in samples
            ]
            return JsonResponse({'result_id': result_id, 'package': str(result.library_version), 'samples': data})
        else:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="time_samples_{result_id}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Iteration', 'Elapsed_NS', 'Elapsed_MS', 'Is_Outlier'])
            for s in samples:
                writer.writerow([s.iteration_number, s.elapsed_nanoseconds, round(s.elapsed_nanoseconds / 1e6, 4), s.is_outlier])
            return response


class CpuMonitorView(View):
    template_name = 'benchmark/cpu_monitor.html'

    def get(self, request, result_id):
        result = get_object_or_404(BenchmarkResult, pk=result_id)
        cpu_samples = result.cpu_samples.all()
        return render(request, self.template_name, {'result': result, 'cpu_samples': cpu_samples})


class MemoryMonitorView(View):
    template_name = 'benchmark/memory_monitor.html'

    def get(self, request, result_id):
        result = get_object_or_404(BenchmarkResult, pk=result_id)
        memory_samples = result.memory_samples.all()
        return render(request, self.template_name, {'result': result, 'memory_samples': memory_samples})


class EnergyMonitorView(View):
    template_name = 'benchmark/energy_monitor.html'

    def get(self, request, result_id):
        result = get_object_or_404(BenchmarkResult, pk=result_id)
        energy_kwh = float(result.energy) / 3.6e6
        return render(request, self.template_name, {'result': result, 'energy_kwh': energy_kwh})


class Co2MonitorView(View):
    template_name = 'benchmark/co2_monitor.html'

    def get(self, request, result_id):
        result = get_object_or_404(BenchmarkResult, pk=result_id)
        return render(request, self.template_name, {'result': result})


class EnergyExportView(View):
    def get(self, request, result_id):
        result = get_object_or_404(BenchmarkResult, pk=result_id)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="energy_telemetry_{result_id}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Result_ID', 'Package', 'Energy_Joules', 'Energy_kWh', 'CO2_Grams'])
        writer.writerow([result.id, str(result.library_version), result.energy, float(result.energy) / 3.6e6, result.co2])
        return response


class ResourceExportView(View):
    def get(self, request, result_id, resource_type):
        result = get_object_or_404(BenchmarkResult, pk=result_id)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{resource_type}_telemetry_{result_id}.csv"'
        writer = csv.writer(response)

        if resource_type == 'cpu':
            writer.writerow(['Sample_Index', 'CPU_Percent', 'Is_Outlier'])
            for s in result.cpu_samples.all():
                writer.writerow([s.sample_index, s.cpu_percent, s.is_outlier])
        else:
            writer.writerow(['Sample_Index', 'RSS_Memory_MB', 'Is_Outlier'])
            for s in result.memory_samples.all():
                writer.writerow([s.sample_index, s.rss_mb, s.is_outlier])

        return response


# --- TASK & DATASET VIEWS ---

class TaskListView(ListView):
    model = BenchmarkTask
    template_name = 'benchmark/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10

    def get_queryset(self):
        return BenchmarkTask.objects.select_related('category', 'dataset').all()


@method_decorator(researcher_required, name='dispatch')
class TaskCreateView(CreateView):
    model = BenchmarkTask
    form_class = BenchmarkTaskForm
    template_name = 'benchmark/task_form.html'
    success_url = reverse_lazy('benchmark:task_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Benchmark Task '{self.object.task_name}' created successfully.")
        return response


class TaskDetailView(DetailView):
    model = BenchmarkTask
    template_name = 'benchmark/task_detail.html'
    context_object_name = 'task'


class DatasetListView(ListView):
    model = BenchmarkDataset
    template_name = 'benchmark/dataset_list.html'
    context_object_name = 'datasets'
    paginate_by = 10

    def get_queryset(self):
        return BenchmarkDataset.objects.select_related('dataset_category').all()


@method_decorator(researcher_required, name='dispatch')
class DatasetCreateView(CreateView):
    model = BenchmarkDataset
    form_class = BenchmarkDatasetForm
    template_name = 'benchmark/dataset_form.html'
    success_url = reverse_lazy('benchmark:dataset_list')

    def form_valid(self, form):
        dataset = form.save(commit=False)
        uploaded_file = self.request.FILES['file_path']
        dataset.dataset_size_bytes = uploaded_file.size
        dataset.checksum_sha256 = calculate_sha256(uploaded_file)
        dataset.save()

        DatasetVersion.objects.create(
            dataset=dataset,
            version_number='1.0.0',
            checksum_sha256=dataset.checksum_sha256,
            file_path=dataset.file_path,
            notes='Initial dataset upload'
        )
        messages.success(self.request, f"Dataset '{dataset.dataset_name}' uploaded successfully! Inspect or download your dataset below.")
        return redirect('benchmark:dataset_preview', pk=dataset.pk)


class DatasetPreviewView(View):
    template_name = 'benchmark/dataset_preview.html'

    def get(self, request, pk):
        dataset = get_object_or_404(BenchmarkDataset, pk=pk)
        mode = request.GET.get('mode', 'head')
        max_lines = 20 if mode == 'head' else None

        preview_data = {
            "lines": [],
            "is_table": False,
            "headers": [],
            "rows": [],
            "total_lines": 0,
            "is_truncated": False
        }

        if dataset.file_path:
            preview_data = DatasetPreviewService.preview_file(dataset.file_path.path, dataset.dataset_type, max_lines=max_lines)

        return render(request, self.template_name, {
            'dataset': dataset,
            'lines': preview_data.get('lines', []),
            'is_table': preview_data.get('is_table', False),
            'headers': preview_data.get('headers', []),
            'rows': preview_data.get('rows', []),
            'total_lines': preview_data.get('total_lines', 0),
            'is_truncated': preview_data.get('is_truncated', False),
            'mode': mode
        })


class DatasetDownloadView(View):
    """Allows downloading the full raw dataset file."""
    def get(self, request, pk):
        dataset = get_object_or_404(BenchmarkDataset, pk=pk)
        if not dataset.file_path or not os.path.exists(dataset.file_path.path):
            messages.error(request, f"File for dataset '{dataset.dataset_name}' was not found on server storage.")
            return redirect('benchmark:dataset_list')

        file_path = dataset.file_path.path
        filename = os.path.basename(file_path)

        content_types = {
            'JSON': 'application/json',
            'CSV': 'text/csv',
            'XML': 'application/xml',
            'TXT': 'text/plain',
            'IMAGE': 'image/png'
        }
        content_type = content_types.get(dataset.dataset_type, 'application/octet-stream')

        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


@method_decorator(researcher_required, name='dispatch')
class DatasetGeneratorView(View):
    template_name = 'benchmark/dataset_generator.html'

    def get(self, request):
        form = DatasetGeneratorForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = DatasetGeneratorForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['dataset_name']
            cat = form.cleaned_data['category']
            lib = form.cleaned_data.get('library')
            dtype = form.cleaned_data['dataset_type']
            count = form.cleaned_data['record_count']
            seed = form.cleaned_data['random_seed']
            user_desc = form.cleaned_data.get('description', '')

            cat_name = cat.category_name if cat else ""
            lib_name = lib.library_name if lib else ""

            content = DeterministicDatasetGenerator.generate_dataset(
                dataset_type=dtype,
                record_count=count,
                seed=seed,
                category_name=cat_name,
                library_name=lib_name,
                dataset_name=name
            )

            ext_map = {'JSON': '.json', 'CSV': '.csv', 'XML': '.xml', 'TXT': '.txt'}
            ext = ext_map.get(dtype, '.json')
            filename = f"{name.lower().replace(' ', '_')}{ext}"

            desc = user_desc or f"Synthetic dataset for category '{cat_name}'"
            if lib_name:
                desc += f" (Target Library: {lib_name})"
            desc += f" [Records: {count}, Seed: {seed}]"

            dataset = BenchmarkDataset.objects.create(
                dataset_name=name,
                dataset_category=cat,
                dataset_type=dtype,
                description=desc,
                dataset_size_bytes=len(content.encode('utf-8'))
            )
            dataset.file_path.save(filename, ContentFile(content))
            dataset.checksum_sha256 = calculate_sha256(dataset.file_path)
            dataset.save()

            messages.success(request, f"Synthetic Dataset '{name}' generated successfully! Inspect or download your dataset below.")
            return redirect('benchmark:dataset_preview', pk=dataset.pk)

        return render(request, self.template_name, {'form': form})


class ProfileListView(ListView):
    model = BenchmarkProfile
    template_name = 'benchmark/profile_list.html'
    context_object_name = 'profiles'
