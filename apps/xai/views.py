from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from apps.xai.models import (
    RecommendationExplanation, SHAPAttributionResult, CounterfactualScenario, DecisionTraceAudit, TrustScoreRecord
)
from apps.xai.forms import ExplanationQueryForm, WhyNotQueryForm
from apps.xai.services.xai_orchestrator_service import XAIOrchestratorService
from apps.xai.services.why_not_service import WhyNotService
from apps.libraries.models import Library

class XAIDashboardView(View):
    template_name = 'xai/xai_dashboard.html'

    def get(self, request):
        context = {
            'total_explanations': RecommendationExplanation.objects.count(),
            'total_shap_models': SHAPAttributionResult.objects.count(),
            'total_traces': DecisionTraceAudit.objects.count(),
            'recent_explanations': RecommendationExplanation.objects.select_related('library', 'category').order_by('-created_at')[:6],
            'trust_records': TrustScoreRecord.objects.select_related('library')[:6]
        }
        return render(request, self.template_name, context)


class ExplanationStudioView(View):
    template_name = 'xai/explanation_studio.html'

    def get(self, request):
        form = ExplanationQueryForm()
        lib_id = request.GET.get('library')
        persona = request.GET.get('persona', 'DEVELOPER')
        packet = None
        library = None

        if lib_id:
            library = get_object_or_404(Library, pk=lib_id)
            form = ExplanationQueryForm(initial={'library': library, 'persona': persona})
            packet = XAIOrchestratorService.generate_full_explanation_packet(library=library, persona=persona)

        context = {
            'form': form,
            'packet': packet,
            'selected_library': library
        }
        return render(request, self.template_name, context)


class CounterfactualSandboxView(View):
    template_name = 'xai/counterfactual_sandbox.html'

    def get(self, request):
        lib_id = request.GET.get('library')
        library = None
        scenarios = []

        if lib_id:
            library = get_object_or_404(Library, pk=lib_id)
            scenarios = CounterfactualScenario.objects.filter(target_library=library)
            if not scenarios.exists():
                scenarios = XAIOrchestratorService.generate_full_explanation_packet(library)['counterfactuals']

        context = {
            'libraries': Library.objects.all(),
            'selected_library': library,
            'scenarios': scenarios
        }
        return render(request, self.template_name, context)


class WhyNotAnalysisView(View):
    template_name = 'xai/why_not_analysis.html'

    def get(self, request):
        form = WhyNotQueryForm()
        unrec_id = request.GET.get('unrecommended_library')
        win_id = request.GET.get('winning_library')
        explanation = None

        if unrec_id and win_id:
            unrec_lib = get_object_or_404(Library, pk=unrec_id)
            win_lib = get_object_or_404(Library, pk=win_id)
            form = WhyNotQueryForm(initial={'unrecommended_library': unrec_lib, 'winning_library': win_lib})
            explanation = WhyNotService.explain_why_not(unrec_lib, win_lib)

        context = {
            'form': form,
            'explanation': explanation
        }
        return render(request, self.template_name, context)


class DecisionTraceDetailView(View):
    template_name = 'xai/decision_trace.html'

    def get(self, request):
        lib_id = request.GET.get('library')
        library = None
        trace = None

        if lib_id:
            library = get_object_or_404(Library, pk=lib_id)
            trace = DecisionTraceAudit.objects.filter(library=library).first()
            if not trace:
                trace = XAIOrchestratorService.generate_full_explanation_packet(library)['trace']

        context = {
            'libraries': Library.objects.all(),
            'selected_library': library,
            'trace': trace
        }
        return render(request, self.template_name, context)


class TrustScoreboardView(ListView):
    model = TrustScoreRecord
    template_name = 'xai/trust_scoreboard.html'
    context_object_name = 'scores'
