from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from apps.authentication.decorators import admin_required, researcher_required
from apps.benchmark.services.comparison_service import ComparisonService
from apps.dashboard.services.analytics_service import AnalyticsService
from apps.dashboard.services.dashboard_service import DashboardService


class WorkspaceRedirectView(LoginRequiredMixin, View):
    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        if request.user.is_superuser or (profile and profile.role and profile.role.role_name == 'ADMIN'):
            return redirect('dashboard:admin_workspace')
        elif profile and profile.role and profile.role.role_name == 'RESEARCHER':
            return redirect('dashboard:researcher_workspace')
        return redirect('dashboard:developer_workspace')


@method_decorator(admin_required, name='dispatch')
class AdminWorkspaceView(View):
    template_name = 'dashboard/admin_workspace.html'

    def get(self, request):
        metrics = DashboardService.get_admin_metrics()
        return render(request, self.template_name, {'metrics': metrics})


@method_decorator(researcher_required, name='dispatch')
class ResearcherWorkspaceView(View):
    template_name = 'dashboard/researcher_workspace.html'

    def get(self, request):
        metrics = DashboardService.get_researcher_metrics()
        return render(request, self.template_name, {'metrics': metrics})


class DeveloperWorkspaceView(View):
    template_name = 'dashboard/developer_workspace.html'

    def get(self, request):
        metrics = DashboardService.get_developer_metrics()
        return render(request, self.template_name, {'metrics': metrics})


class AnalyticsDashboardView(View):
    template_name = 'dashboard/analytics_dashboard.html'

    def get(self, request):
        chart_data = AnalyticsService.get_chart_telemetry()
        return render(request, self.template_name, {'chart_data': chart_data})


class ComparisonStudioView(View):
    template_name = 'dashboard/comparison_studio.html'

    def get(self, request):
        result_ids = request.GET.getlist('ids')
        comparison = {}
        if result_ids:
            comparison = ComparisonService.compare_results(result_ids)
        return render(request, self.template_name, {'comparison': comparison})
