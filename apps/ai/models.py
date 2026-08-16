from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel, StatusChoices
from apps.libraries.models import Library, Category, ProgrammingLanguage

class PredictionTargetChoices(models.TextChoices):
    GREEN_SCORE = 'GREEN_SCORE', 'Multi-Criteria Green Score (0-100)'
    ENERGY_JOULES = 'ENERGY_JOULES', 'Package Energy Consumption (Joules)'
    EXECUTION_TIME_MS = 'EXECUTION_TIME_MS', 'Execution Latency (Milliseconds)'
    RAM_RSS_MB = 'RAM_RSS_MB', 'RAM Resident Set Size (MB)'
    CPU_UTILIZATION_PCT = 'CPU_UTILIZATION_PCT', 'CPU Utilization (%)'


class ModelAlgorithmChoices(models.TextChoices):
    RIDGE_REGRESSION = 'RIDGE_REGRESSION', 'L2-Regularized Ridge Regression'
    RANDOM_FOREST = 'RANDOM_FOREST', 'Ensemble Random Forest Regressor'
    GRADIENT_BOOSTING = 'GRADIENT_BOOSTING', 'Gradient Boosted Decision Trees'
    LINEAR_REGRESSION = 'LINEAR_REGRESSION', 'Ordinary Least Squares Regression'


class AIPredictionModel(TimeStampedModel):
    """Stores trained predictive sustainability machine learning models and evaluation metrics."""
    model_name = models.CharField(max_length=150)
    version = models.CharField(max_length=20, default='1.0.0')
    algorithm = models.CharField(max_length=30, choices=ModelAlgorithmChoices.choices, default=ModelAlgorithmChoices.RIDGE_REGRESSION)
    target_metric = models.CharField(max_length=30, choices=PredictionTargetChoices.choices, default=PredictionTargetChoices.GREEN_SCORE)
    
    # Model evaluation metrics
    r2_score = models.FloatField(default=0.0, help_text="Coefficient of Determination R^2")
    rmse = models.FloatField(default=0.0, help_text="Root Mean Squared Error")
    mae = models.FloatField(default=0.0, help_text="Mean Absolute Error")
    mape = models.FloatField(default=0.0, help_text="Mean Absolute Percentage Error (%)")
    
    # Model serialization weights & feature schema
    feature_names = models.JSONField(default=list, help_text="Ordered list of feature column names")
    feature_weights = models.JSONField(default=dict, help_text="Feature importance weights or linear coefficients")
    model_parameters = models.JSONField(default=dict, help_text="Trained model coefficients/hyperparameters")
    
    is_active = models.BooleanField(default=True, help_text="Active model for online inference")

    class Meta:
        verbose_name = "AI Prediction Model"
        verbose_name_plural = "AI Prediction Models"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.model_name} v{self.version} ({self.get_target_metric_display()}) [R2: {self.r2_score:.3f}]"


class ModelTrainingRun(TimeStampedModel):
    """Audit log tracking model training experiments, splits, and validation results."""
    model = models.ForeignKey(AIPredictionModel, on_delete=models.CASCADE, related_name='training_runs')
    training_sample_size = models.PositiveIntegerField()
    test_sample_size = models.PositiveIntegerField()
    duration_seconds = models.FloatField(default=0.0)
    train_r2 = models.FloatField(default=0.0)
    val_r2 = models.FloatField(default=0.0)
    hyperparameters = models.JSONField(default=dict)
    training_log = models.TextField(blank=True)

    class Meta:
        verbose_name = "Model Training Run"
        verbose_name_plural = "Model Training Runs"
        ordering = ['-created_at']


class FeatureRecord(TimeStampedModel):
    """Centralized feature store storing engineered feature vectors for libraries."""
    library = models.OneToOneField(Library, on_delete=models.CASCADE, related_name='feature_record')
    lines_of_code = models.PositiveIntegerField(default=10000)
    dependency_count = models.PositiveIntegerField(default=2)
    popularity_score = models.PositiveIntegerField(default=100)
    category_id_val = models.IntegerField(default=1)
    language_id_val = models.IntegerField(default=1)
    feature_vector = models.JSONField(default=dict, help_text="Normalized numerical feature array")

    class Meta:
        verbose_name = "Feature Record"
        verbose_name_plural = "Feature Records"

    def __str__(self):
        return f"Features for {self.library.library_name}"


class SustainabilityPrediction(TimeStampedModel):
    """Auditable prediction record. Explicitly separated from empirical benchmark ground truth."""
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='ai_predictions')
    target_metric = models.CharField(max_length=30, choices=PredictionTargetChoices.choices)
    predicted_value = models.FloatField(help_text="Predicted numerical metric value")
    confidence_score = models.FloatField(default=0.0, help_text="Prediction confidence index (0-100%)")
    model_used = models.ForeignKey(AIPredictionModel, on_delete=models.SET_NULL, null=True, related_name='predictions')
    
    # Explainable AI (XAI)
    explanation_text = models.TextField(help_text="Human-readable explanation of why this prediction was made")
    feature_attribution = models.JSONField(default=dict, help_text="SHAP-style relative feature contributions")
    
    # Ground truth validation link (if later empirically measured)
    actual_measured_value = models.FloatField(null=True, blank=True, help_text="Actual physical measurement if later benchmarked")
    prediction_error_pct = models.FloatField(null=True, blank=True, help_text="Absolute percentage error |Pred - Actual| / Actual")

    class Meta:
        verbose_name = "Sustainability Prediction"
        verbose_name_plural = "Sustainability Predictions"
        ordering = ['-created_at']

    def __str__(self):
        return f"PREDICTED: {self.library.library_name} -> {self.get_target_metric_display()}: {self.predicted_value:.2f} (Conf: {self.confidence_score:.1f}%)"


class DriftReport(TimeStampedModel):
    """Audit log assessing model accuracy decay, feature drift, and ground-truth divergence."""
    model = models.ForeignKey(AIPredictionModel, on_delete=models.CASCADE, related_name='drift_reports')
    total_evaluated_samples = models.PositiveIntegerField()
    mean_prediction_error_pct = models.FloatField(help_text="Mean absolute percentage error across evaluated predictions")
    feature_drift_score = models.FloatField(default=0.0, help_text="Wasserstein / KS feature drift distance (0-1.0)")
    drift_detected = models.BooleanField(default=False)
    recommendation_notes = models.TextField()

    class Meta:
        verbose_name = "Model Drift Report"
        verbose_name_plural = "Model Drift Reports"
        ordering = ['-created_at']
