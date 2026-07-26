from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.files.base import ContentFile
from django.utils.decorators import method_decorator

from apps.benchmark.models import (
    BenchmarkSession, BenchmarkJob, BenchmarkResult, BenchmarkTask,
    BenchmarkDataset, DatasetVersion, BenchmarkProfile
)
from apps.benchmark.forms import (
    BenchmarkSessionForm, BenchmarkTaskForm, BenchmarkDatasetForm,
    DatasetGeneratorForm, BenchmarkProfileForm
)
from apps.benchmark.services.session_service import SessionService
from apps.benchmark.services.environment_service import EnvironmentService
from apps.benchmark.services.dataset_generator import DeterministicDatasetGenerator
from apps.benchmark.services.dataset_preview import DatasetPreviewService
from apps.benchmark.validators import calculate_sha256
from apps.benchmark.runner.runner import BenchmarkRunner
from apps.core.models import AuditLog
from apps.authentication.decorators import researcher_required, admin_required

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
        return BenchmarkJob.objects.select_related('session', 'library_version__library', 'task').order_by('status', 'priority')


# --- RUNNER SPECIFIC VIEWS ---

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
        messages.success(self.request, f"Dataset '{dataset.dataset_name}' uploaded successfully.")
        return redirect('benchmark:dataset_list')


class DatasetPreviewView(View):
    template_name = 'benchmark/dataset_preview.html'

    def get(self, request, pk):
        dataset = get_object_or_404(BenchmarkDataset, pk=pk)
        lines = []
        if dataset.file_path:
            lines = DatasetPreviewService.preview_file(dataset.file_path.path, dataset.dataset_type)
        return render(request, self.template_name, {'dataset': dataset, 'lines': lines})


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
            dtype = form.cleaned_data['dataset_type']
            count = form.cleaned_data['record_count']
            seed = form.cleaned_data['random_seed']

            if dtype == 'JSON':
                content = DeterministicDatasetGenerator.generate_json(record_count=count, seed=seed)
                filename = f"{name.lower().replace(' ', '_')}.json"
            else:
                content = DeterministicDatasetGenerator.generate_csv(record_count=count, seed=seed)
                filename = f"{name.lower().replace(' ', '_')}.csv"

            dataset = BenchmarkDataset.objects.create(
                dataset_name=name,
                dataset_category=cat,
                dataset_type=dtype,
                description=f"Generated synthetically with seed={seed}, record_count={count}",
                dataset_size_bytes=len(content.encode('utf-8'))
            )
            dataset.file_path.save(filename, ContentFile(content))
            dataset.checksum_sha256 = calculate_sha256(dataset.file_path)
            dataset.save()

            messages.success(request, f"Synthetic Dataset '{name}' generated cleanly with SHA256 checksum!")
            return redirect('benchmark:dataset_list')

        return render(request, self.template_name, {'form': form})


class ProfileListView(ListView):
    model = BenchmarkProfile
    template_name = 'benchmark/profile_list.html'
    context_object_name = 'profiles'
