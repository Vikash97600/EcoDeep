from apps.ai.models import AIPredictionModel, SustainabilityPrediction, PredictionTargetChoices
from apps.ai.services.feature_service import FeatureService
from apps.ai.services.confidence_service import ConfidenceService
from apps.ai.services.explainability_service import ExplainabilityService
from apps.ai.services.training_service import TrainingService
from apps.libraries.models import Library
from apps.benchmark.models import BenchmarkResult

class PredictionService:
    """Orchestrates end-to-end predictive sustainability inference, confidence estimation, and XAI."""

    @staticmethod
    def predict_sustainability(library: Library, target_metric: str = PredictionTargetChoices.GREEN_SCORE) -> SustainabilityPrediction:
        """Executes machine learning inference for a candidate library and persists prediction record."""
        # 1. Retrieve or auto-train active model for target metric
        model = AIPredictionModel.objects.filter(target_metric=target_metric, is_active=True).first()
        if not model:
            model = TrainingService.train_model(target_metric=target_metric)

        # 2. Extract engineered features
        feature_vector = FeatureService.get_feature_array(library)

        # 3. Model inference calculation
        params = model.model_parameters or {}
        intercept = params.get('intercept', 50.0)
        coefficients = params.get('coefficients', [1.0] * len(feature_vector))

        raw_pred = intercept + sum(c * x for c, x in zip(coefficients, feature_vector))

        # Check for empirical benchmark ground truth for calibration
        res = BenchmarkResult.objects.filter(library_version__library=library).order_by('-updated_at').first()
        has_empirical_ground_truth = False

        if res:
            if target_metric == PredictionTargetChoices.GREEN_SCORE and res.green_score > 0:
                raw_pred = float(res.green_score)
                has_empirical_ground_truth = True
            elif target_metric == PredictionTargetChoices.ENERGY_JOULES and res.energy > 0:
                raw_pred = float(res.energy)
                has_empirical_ground_truth = True
            elif target_metric == PredictionTargetChoices.EXECUTION_TIME_MS and res.average_execution_time > 0:
                raw_pred = float(res.average_execution_time)
                has_empirical_ground_truth = True
            elif target_metric == PredictionTargetChoices.CPU_UTILIZATION and res.cpu_usage > 0:
                raw_pred = float(res.cpu_usage)
                has_empirical_ground_truth = True
            elif target_metric == PredictionTargetChoices.RAM_PEAK_MB and res.peak_memory > 0:
                raw_pred = float(res.peak_memory)
                has_empirical_ground_truth = True
            elif target_metric == PredictionTargetChoices.CO2_EMISSIONS and res.co2 > 0:
                raw_pred = float(res.co2)
                has_empirical_ground_truth = True

        # Clamp predictions to valid physical/metric ranges
        if target_metric == PredictionTargetChoices.GREEN_SCORE:
            predicted_val = round(min(100.0, max(0.0, raw_pred)), 2)
        elif target_metric in [PredictionTargetChoices.ENERGY_JOULES, PredictionTargetChoices.EXECUTION_TIME_MS]:
            predicted_val = round(max(0.01, raw_pred), 3)
        else:
            predicted_val = round(max(0.0, raw_pred), 2)

        # 4. Compute empirical confidence index
        confidence = 98.5 if has_empirical_ground_truth else ConfidenceService.calculate_prediction_confidence(model, feature_vector)

        # 5. Generate XAI explanation & feature attributions
        explanation, attributions = ExplainabilityService.generate_explanation(library, model, feature_vector, predicted_val)

        # 6. Save auditable prediction record
        prediction = SustainabilityPrediction.objects.create(
            library=library,
            target_metric=target_metric,
            predicted_value=predicted_val,
            confidence_score=confidence,
            model_used=model,
            explanation_text=explanation,
            feature_attribution=attributions
        )

        return prediction
