from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.decorators import method_decorator

from apps.benchmark.models import BenchmarkSession, BenchmarkJob, BenchmarkResult, BenchmarkTask, BenchmarkDataset
from apps.benchmark.forms import BenchmarkSessionForm
from apps.benchmark.services.session_service import SessionService
from apps.benchmark.services.environment_service import EnvironmentService
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
            'pending_jobs': BenchmarkJob.objects.filter(status='PENDING').count(),
            'total_results': BenchmarkResult.objects.count(),
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
