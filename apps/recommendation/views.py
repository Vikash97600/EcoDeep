from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.http import JsonResponse

from apps.recommendation.models import GreenScore, WeightProfile, ScoringStrategyChoices, RecommendationRecord, RecommendationItem
from apps.recommendation.forms import WeightProfileForm, RecommendationQueryForm
from apps.recommendation.services.greenscore_service import GreenScoreService
from apps.recommendation.services.recommendation_service import RecommendationService
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


# --- INTELLIGENT RECOMMENDATION VIEWS ---

class RecommendationQueryView(View):
    template_name = 'recommendation/recommendation_query.html'

    def get(self, request):
        form = RecommendationQueryForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RecommendationQueryForm(request.POST)
        if form.is_valid():
            user = request.user if request.user.is_authenticated else None
            rec_record = RecommendationService.generate_recommendation(
                target_library_id=form.cleaned_data['target_library'].id,
                task_id=form.cleaned_data['task'].id,
                profile_type=form.cleaned_data['profile_type'],
                user=user
            )
            messages.success(request, f"Recommendation generated successfully for {rec_record.target_library.library_name}!")
            return redirect('recommendation:recommend_detail', pk=rec_record.id)

        return render(request, self.template_name, {'form': form})


class RecommendationDetailView(DetailView):
    model = RecommendationRecord
    template_name = 'recommendation/recommendation_detail.html'
    context_object_name = 'record'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('recommended_version__library').all()
        return context


class RecommendationHistoryListView(ListView):
    model = RecommendationRecord
    template_name = 'recommendation/recommendation_history.html'
    context_object_name = 'records'
    paginate_by = 10

    def get_queryset(self):
        return RecommendationRecord.objects.select_related('target_library', 'task', 'user').order_by('-created_at')


class APIRecommendationQueryView(View):
    def get(self, request):
        target_id = request.GET.get('target_library')
        task_id = request.GET.get('task')
        profile_type = request.GET.get('profile', 'BEST_OVERALL')

        if not target_id or not task_id:
            return JsonResponse({'error': 'Missing target_library or task parameter.'}, status=400)

        rec_record = RecommendationService.generate_recommendation(
            target_library_id=int(target_id),
            task_id=int(task_id),
            profile_type=profile_type
        )

        items_data = [
            {
                'rank': item.rank,
                'recommended_package': str(item.recommended_version),
                'green_score': float(item.green_score),
                'confidence_score': float(item.confidence_score),
                'explanation': item.explanation_text,
                'is_top_choice': item.is_top_choice
            }
            for item in rec_record.items.all()
        ]

        return JsonResponse({
            'recommendation_id': rec_record.id,
            'target_library': rec_record.target_library.library_name,
            'task': rec_record.task.task_name,
            'profile_type': rec_record.recommendation_profile,
            'recommendations': items_data
        })
