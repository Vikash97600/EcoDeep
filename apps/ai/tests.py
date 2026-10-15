from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apps.ai.models import (
    PredictionTargetChoices,
    SustainabilityPrediction,
)
from apps.ai.services.confidence_service import ConfidenceService
from apps.ai.services.drift_service import DriftService
from apps.ai.services.evaluation_service import EvaluationService
from apps.ai.services.explainability_service import ExplainabilityService
from apps.ai.services.feature_service import FeatureService
from apps.ai.services.prediction_service import PredictionService
from apps.ai.services.training_service import TrainingService
from apps.benchmark.models import (
    BenchmarkDataset,
    BenchmarkResult,
    BenchmarkSession,
    BenchmarkStatusChoices,
    BenchmarkTask,
)
from apps.libraries.models import Category, Library, LibraryVersion, ProgrammingLanguage
from apps.users.models import Role, RoleChoices, UserProfile


class AIPredictiveSustainabilityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.researcher_role = Role.objects.create(role_name=RoleChoices.RESEARCHER)
        self.user = User.objects.create_user(username='ai_researcher', password='Password123!')
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.role = self.researcher_role
        profile.save()

        self.lang = ProgrammingLanguage.objects.create(language_name='Python', slug='python')
        self.cat = Category.objects.create(category_name='Serialization', slug='serialization')
        self.lib = Library.objects.create(
            library_name='orjson_fast',
            official_name='orjson_fast',
            current_version='3.8.0',
            programming_language=self.lang,
            category=self.cat,
            popularity_score=850
        )

    def test_feature_service(self):
        record = FeatureService.get_or_create_feature_record(self.lib)
        self.assertEqual(record.library, self.lib)
        
        feat_array = FeatureService.get_feature_array(self.lib)
        self.assertEqual(len(feat_array), len(FeatureService.FEATURE_NAMES))
        self.assertGreater(feat_array[0], 0.0)

    def test_evaluation_service(self):
        y_true = [10.0, 20.0, 30.0, 40.0, 50.0]
        y_pred = [11.0, 19.0, 31.0, 39.0, 51.0]
        metrics = EvaluationService.evaluate_regression(y_true, y_pred)
        
        self.assertGreater(metrics['r2'], 0.9)
        self.assertGreater(metrics['rmse'], 0.0)
        self.assertGreater(metrics['mae'], 0.0)

    def test_model_training_and_registry(self):
        model = TrainingService.train_model(target_metric=PredictionTargetChoices.GREEN_SCORE)
        self.assertIsNotNone(model)
        self.assertTrue(model.is_active)
        self.assertGreater(model.r2_score, 0.0)
        self.assertTrue(model.training_runs.exists())

    def test_confidence_and_explainability_services(self):
        model = TrainingService.train_model(target_metric=PredictionTargetChoices.GREEN_SCORE)
        feats = FeatureService.get_feature_array(self.lib)
        
        confidence = ConfidenceService.calculate_prediction_confidence(model, feats)
        self.assertGreaterEqual(confidence, 35.0)
        self.assertLessEqual(confidence, 100.0)

        narrative, attributions = ExplainabilityService.generate_explanation(self.lib, model, feats, 88.5)
        self.assertIn('orjson_fast', narrative)
        self.assertEqual(len(attributions), len(FeatureService.FEATURE_NAMES))

    def test_end_to_end_prediction_service(self):
        prediction = PredictionService.predict_sustainability(self.lib, target_metric=PredictionTargetChoices.GREEN_SCORE)
        self.assertIsNotNone(prediction)
        self.assertEqual(prediction.library, self.lib)
        self.assertGreater(prediction.predicted_value, 0.0)
        self.assertGreater(prediction.confidence_score, 0.0)
        self.assertTrue(SustainabilityPrediction.objects.filter(library=self.lib).exists())

    def test_all_prediction_target_metrics(self):
        """Verifies prediction inference for all target metrics including RAM and CPU without errors."""
        metrics = [
            PredictionTargetChoices.GREEN_SCORE,
            PredictionTargetChoices.ENERGY_JOULES,
            PredictionTargetChoices.EXECUTION_TIME_MS,
            PredictionTargetChoices.RAM_RSS_MB,
            PredictionTargetChoices.CPU_UTILIZATION_PCT,
        ]
        for metric in metrics:
            pred = PredictionService.predict_sustainability(self.lib, target_metric=metric)
            self.assertIsNotNone(pred)
            self.assertEqual(pred.target_metric, metric)
            self.assertGreater(pred.predicted_value, 0.0)
            self.assertGreater(pred.confidence_score, 0.0)

    def test_empirical_benchmark_ground_truth_calibration(self):
        """Verifies that empirical ground-truth telemetry calibrates RAM and CPU predictions."""
        version = LibraryVersion.objects.create(library=self.lib, version_number='3.8.0')
        dataset = BenchmarkDataset.objects.create(
            dataset_name='Payload 5MB',
            dataset_category=self.cat,
            dataset_size_bytes=5242880
        )
        task = BenchmarkTask.objects.create(
            task_name='Serialization 5MB',
            category=self.cat,
            dataset=dataset
        )
        session = BenchmarkSession.objects.create(
            session_name='GroundTruth Session',
            status=BenchmarkStatusChoices.COMPLETED
        )
        BenchmarkResult.objects.create(
            session=session,
            library_version=version,
            task=task,
            dataset=dataset,
            peak_memory=48.25,
            average_memory=40.0,
            cpu_usage=31.5,
            average_cpu=29.8,
            average_execution_time=55.0,
            energy=4.2,
            green_score=92.5
        )

        # Test RAM calibration
        pred_ram = PredictionService.predict_sustainability(self.lib, target_metric=PredictionTargetChoices.RAM_RSS_MB)
        self.assertEqual(pred_ram.predicted_value, 48.25)
        self.assertEqual(pred_ram.confidence_score, 98.5)

        # Test CPU calibration
        pred_cpu = PredictionService.predict_sustainability(self.lib, target_metric=PredictionTargetChoices.CPU_UTILIZATION_PCT)
        self.assertEqual(pred_cpu.predicted_value, 29.8)
        self.assertEqual(pred_cpu.confidence_score, 98.5)

    def test_prediction_target_aliases_backward_compatibility(self):
        """Ensures CPU_UTILIZATION and RAM_PEAK_MB aliases resolve correctly."""
        self.assertEqual(PredictionTargetChoices.CPU_UTILIZATION, PredictionTargetChoices.CPU_UTILIZATION_PCT)
        self.assertEqual(PredictionTargetChoices.RAM_PEAK_MB, PredictionTargetChoices.RAM_RSS_MB)

    def test_predict_view_post_ram_and_cpu(self):
        """Tests that submitting RAM_RSS_MB and CPU_UTILIZATION_PCT via HTTP POST succeeds."""
        self.client.login(username='ai_researcher', password='Password123!')
        
        # Post RAM_RSS_MB
        res_ram = self.client.post(reverse('ai:predict_sustainability'), {
            'library': self.lib.id,
            'target_metric': PredictionTargetChoices.RAM_RSS_MB
        })
        self.assertEqual(res_ram.status_code, 200)
        self.assertIn('prediction', res_ram.context)
        self.assertEqual(res_ram.context['prediction'].target_metric, PredictionTargetChoices.RAM_RSS_MB)

        # Post CPU_UTILIZATION_PCT
        res_cpu = self.client.post(reverse('ai:predict_sustainability'), {
            'library': self.lib.id,
            'target_metric': PredictionTargetChoices.CPU_UTILIZATION_PCT
        })
        self.assertEqual(res_cpu.status_code, 200)
        self.assertIn('prediction', res_cpu.context)
        self.assertEqual(res_cpu.context['prediction'].target_metric, PredictionTargetChoices.CPU_UTILIZATION_PCT)

    def test_drift_service(self):
        model = TrainingService.train_model(target_metric=PredictionTargetChoices.GREEN_SCORE)
        drift_report = DriftService.audit_model_drift(model)
        self.assertIsNotNone(drift_report)
        self.assertEqual(drift_report.model, model)

    def test_ai_dashboard_and_views(self):
        self.client.login(username='ai_researcher', password='Password123!')
        res_dash = self.client.get(reverse('ai:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_reg = self.client.get(reverse('ai:model_registry'))
        self.assertEqual(res_reg.status_code, 200)

        res_pred = self.client.get(reverse('ai:predict_sustainability'))
        self.assertEqual(res_pred.status_code, 200)

        res_drift = self.client.get(reverse('ai:drift_monitor'))
        self.assertEqual(res_drift.status_code, 200)

