from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from apps.recommendation.models import GreenScore, WeightProfile, ScoringStrategyChoices
from apps.recommendation.forms import WeightProfileForm
from apps.recommendation.services.greenscore_service import GreenScoreService
from apps.authentication.decorators import researcher_required

class GreenScoreDashboardView(View):
    template_name = 'recommendation/greenscore_dashboard.html'

    def get(self, request):
        context = {
            'total_scores': GreenScore.objects.count(),
            'top_scores': GreenScore.objects.select_related('library_version__library', 'task').order_by('-score')[:10],
            'profiles': WeightProfile.objects.all(),
        }
        return render(request, self.template_name, context)


@method_decorator(researcher_required, name='dispatch')
class CalculateGreenScoreView(View):
    def post(self, request, session_id):
        strategy = request.POST.get('strategy', 'TOPSIS')
        profile_name = request.POST.get('profile')

        scores = GreenScoreService.calculate_session_greenscores(
            session_id=session_id,
            strategy_name=strategy,
            profile_name=profile_name
        )
        messages.success(request, f"Green Scores calculated using {strategy} for Session #{session_id}!")
        return redirect('benchmark:session_detail', pk=session_id)


class WeightProfileListView(ListView):
    model = WeightProfile
    template_name = 'recommendation/weight_profiles.html'
    context_object_name = 'profiles'


@method_decorator(researcher_required, name='dispatch')
class WeightProfileCreateView(CreateView):
    model = WeightProfile
    form_class = WeightProfileForm
    template_name = 'recommendation/weight_profile_form.html'
    success_url = reverse_lazy('recommendation:weight_profiles')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Weight Profile '{self.object.profile_name}' created successfully.")
        return response


class RankingTableView(ListView):
    model = GreenScore
    template_name = 'recommendation/ranking_table.html'
    context_object_name = 'rankings'
    paginate_by = 15

    def get_queryset(self):
        return GreenScore.objects.select_related('library_version__library', 'task', 'weight_profile').order_by('-score')
