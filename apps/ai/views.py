from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.ai.forms import ModelTrainingForm, SustainabilityPredictionForm
from apps.ai.models import (
    AIPredictionModel,
    DriftReport,
    ModelTrainingRun,
    SustainabilityPrediction,
)
from apps.ai.services.prediction_service import PredictionService
from apps.ai.services.training_service import TrainingService
from apps.authentication.decorators import admin_required, researcher_required


class AIPredictionDashboardView(View):
    template_name = 'ai/ai_dashboard.html'

    def get(self, request):
        context = {
            'total_models': AIPredictionModel.objects.count(),
            'active_models': AIPredictionModel.objects.filter(is_active=True).count(),
            'total_predictions': SustainabilityPrediction.objects.count(),
            'recent_predictions': SustainabilityPrediction.objects.select_related('library', 'model_used').order_by('-created_at')[:8],
            'recent_training_runs': ModelTrainingRun.objects.select_related('model').order_by('-created_at')[:5],
            'recent_drift_reports': DriftReport.objects.select_related('model').order_by('-created_at')[:4]
        }
        return render(request, self.template_name, context)


class ModelRegistryListView(ListView):
    model = AIPredictionModel
    template_name = 'ai/model_registry.html'
    context_object_name = 'models'


class ModelDetailView(DetailView):
    model = AIPredictionModel
    template_name = 'ai/model_detail.html'
    context_object_name = 'model'


@method_decorator(researcher_required, name='dispatch')
class PredictSustainabilityView(View):
    template_name = 'ai/predict_sustainability.html'

    def get(self, request):
        form = SustainabilityPredictionForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = SustainabilityPredictionForm(request.POST)
        if form.is_valid():
            library = form.cleaned_data['library']
            target_metric = form.cleaned_data['target_metric']
            prediction = PredictionService.predict_sustainability(library, target_metric)
            messages.success(request, f"AI prediction generated for '{library.library_name}' with {prediction.confidence_score}% confidence!")
            return render(request, self.template_name, {'form': form, 'prediction': prediction})
        return render(request, self.template_name, {'form': form})


@method_decorator(admin_required, name='dispatch')
class ModelTrainView(View):
    template_name = 'ai/model_train.html'

    def get(self, request):
        form = ModelTrainingForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ModelTrainingForm(request.POST)
        if form.is_valid():
            algorithm = form.cleaned_data['algorithm']
            target_metric = form.cleaned_data['target_metric']
            model = TrainingService.train_model(target_metric=target_metric, algorithm=algorithm)
            messages.success(request, f"Successfully trained and registered model '{model.model_name}' (R2: {model.r2_score:.3f})!")
            return redirect('ai:model_detail', pk=model.pk)
        return render(request, self.template_name, {'form': form})


class DriftMonitoringView(ListView):
    model = DriftReport
    template_name = 'ai/drift_monitor.html'
    context_object_name = 'drift_reports'
