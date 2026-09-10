from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from apps.authentication.decorators import researcher_required
from apps.libraries.models import Category
from apps.mcdm.forms import MCDMRankingQueryForm, WeightProfileForm
from apps.mcdm.models import MCDMEvaluationRun, MCDMWeightProfile
from apps.mcdm.services.ahp_service import AHPService
from apps.mcdm.services.ranking_service import RankingService
from apps.mcdm.services.sensitivity_service import SensitivityService
from apps.mcdm.services.weight_service import WeightService


class MCDMDashboardView(View):
    template_name = 'mcdm/mcdm_dashboard.html'

    def get(self, request):
        WeightService.get_or_create_default_profiles()
        context = {
            'total_evaluations': MCDMEvaluationRun.objects.count(),
            'total_profiles': MCDMWeightProfile.objects.count(),
            'recent_evaluations': MCDMEvaluationRun.objects.select_related('category', 'weight_profile').order_by('-created_at')[:8],
            'profiles': MCDMWeightProfile.objects.filter(is_active=True)
        }
        return render(request, self.template_name, context)


class MCDMRankingStudioView(View):
    template_name = 'mcdm/ranking_studio.html'

    def get(self, request):
        WeightService.get_or_create_default_profiles()
        form = MCDMRankingQueryForm()
        cat_id = request.GET.get('category')
        eval_run = None

        if cat_id:
            category = get_object_or_404(Category, pk=cat_id)
            profile_id = request.GET.get('weight_profile')
            profile = MCDMWeightProfile.objects.filter(pk=profile_id).first() if profile_id else None
            method = request.GET.get('mcdm_method', 'TOPSIS')

            eval_run = RankingService.execute_mcdm_ranking(category=category, profile=profile, method=method)
            form = MCDMRankingQueryForm(initial={'category': category, 'weight_profile': eval_run.weight_profile, 'mcdm_method': method})

        context = {
            'form': form,
            'eval_run': eval_run,
            'recent_runs': MCDMEvaluationRun.objects.select_related('category', 'weight_profile')[:5]
        }
        return render(request, self.template_name, context)


class MCDMEvaluationDetailView(DetailView):
    model = MCDMEvaluationRun
    template_name = 'mcdm/evaluation_detail.html'
    context_object_name = 'eval_run'


class WeightProfileListView(ListView):
    model = MCDMWeightProfile
    template_name = 'mcdm/weight_profiles.html'
    context_object_name = 'profiles'


@method_decorator(researcher_required, name='dispatch')
class WeightProfileCreateView(CreateView):
    model = MCDMWeightProfile
    form_class = WeightProfileForm
    template_name = 'mcdm/weight_profile_form.html'
    success_url = reverse_lazy('mcdm:weight_profiles')

    def form_valid(self, form):
        messages.success(self.request, f"Weight profile '{form.cleaned_data['profile_name']}' saved successfully!")
        return super().form_valid(form)


class AHPMatrixCalculatorView(View):
    template_name = 'mcdm/ahp_calculator.html'

    def get(self, request):
        matrix = AHPService.get_default_ahp_matrix()
        weights, ci, cr, is_consistent = AHPService.calculate_ahp_weights(matrix)
        context = {
            'matrix': matrix,
            'weights': weights,
            'ci': ci,
            'cr': cr,
            'is_consistent': is_consistent,
            'criteria': AHPService.CRITERIA
        }
        return render(request, self.template_name, context)


class SensitivityAnalysisView(View):
    template_name = 'mcdm/sensitivity_analysis.html'

    def get(self, request):
        eval_id = request.GET.get('evaluation_id')
        eval_run = MCDMEvaluationRun.objects.filter(pk=eval_id).first() if eval_id else MCDMEvaluationRun.objects.first()
        report = None

        if eval_run:
            criterion = request.GET.get('criterion', 'energy_joules')
            perturbation = float(request.GET.get('perturbation', 20.0))
            report = SensitivityService.audit_ranking_sensitivity(eval_run, criterion_to_perturb=criterion, perturbation_pct=perturbation)

        context = {
            'eval_run': eval_run,
            'report': report,
            'recent_evaluations': MCDMEvaluationRun.objects.all()[:5]
        }
        return render(request, self.template_name, context)
