from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apps.benchmark.models import BenchmarkDataset, BenchmarkTask
from apps.experiments.models import ScientificExperiment
from apps.experiments.services.confidence_service import ConfidenceService
from apps.experiments.services.experiment_service import ExperimentService
from apps.experiments.services.outlier_service import OutlierService
from apps.experiments.services.statistics_service import StatisticsService
from apps.experiments.services.validation_service import ValidationService
from apps.libraries.models import Category, Library, ProgrammingLanguage
from apps.users.models import Role, RoleChoices, UserProfile


class ScientificExperimentsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.researcher_role = Role.objects.create(role_name=RoleChoices.RESEARCHER)
        self.user = User.objects.create_user(username='res_user', password='Password123!')
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.role = self.researcher_role
        profile.save()

        self.lang = ProgrammingLanguage.objects.create(language_name='Python', slug='python')
        self.cat = Category.objects.create(category_name='JSON Parsers', slug='json-parsers')
        self.lib_a = Library.objects.create(library_name='json_std', official_name='json_std', current_version='1.0.0', programming_language=self.lang, category=self.cat)
        self.lib_b = Library.objects.create(library_name='ujson_fast', official_name='ujson_fast', current_version='1.0.0', programming_language=self.lang, category=self.cat)

        self.b_dataset = BenchmarkDataset.objects.create(
            dataset_name='Test JSON Data',
            dataset_category=self.cat,
            dataset_size_bytes=1024,
            description='Test dataset'
        )
        self.task = BenchmarkTask.objects.create(
            task_name='Parse 100k Records',
            category=self.cat,
            dataset=self.b_dataset,
            description='Benchmark workload task',
            expected_output='dict'
        )

        self.experiment = ScientificExperiment.objects.create(
            title='JSON Parser Benchmark',
            researcher=self.user,
            research_question='Is ujson faster and more energy efficient than json?',
            null_hypothesis='H0: Energy(ujson) == Energy(json)',
            alternative_hypothesis='H1: Energy(ujson) < Energy(json)',
            benchmark_task=self.task,
            warmup_iterations=2,
            measurement_iterations=10,
            random_seed=123
        )
        self.experiment.candidate_libraries.add(self.lib_a, self.lib_b)

    def test_outlier_detection_algorithms(self):
        sample = [10.0, 10.2, 10.1, 10.3, 10.2, 10.1, 95.0]  # 95.0 is an outlier
        iqr_outliers = OutlierService.detect_iqr_outliers(sample)
        OutlierService.detect_zscore_outliers(sample)
        mad_outliers = OutlierService.detect_mad_outliers(sample)
        
        self.assertTrue(iqr_outliers[-1])
        self.assertTrue(mad_outliers[-1])

    def test_statistics_service_calculations(self):
        sample = [10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 11.0]
        stats = StatisticsService.compute_descriptive_stats(sample)
        
        self.assertEqual(stats['sample_size'], 7)
        self.assertGreater(stats['mean'], 0)
        self.assertIn('ci_95_lower', stats)
        self.assertIn('coefficient_of_variation', stats)

    def test_inferential_ttest_and_effect_size(self):
        sample_a = [100.0, 102.0, 101.0, 99.0, 103.0]
        sample_b = [50.0, 52.0, 51.0, 49.0, 53.0]
        
        ttest = StatisticsService.compute_two_sample_ttest(sample_a, sample_b)
        effect = StatisticsService.compute_cohens_d(sample_a, sample_b)
        
        self.assertTrue(ttest['reject_null'])
        self.assertEqual(effect['magnitude'], 'Large')

    def test_confidence_and_validation_service(self):
        confidence = ConfidenceService.calculate_confidence_index(30, 5.0, 0, 30)
        self.assertGreater(confidence, 80.0)

        records = [{'execution_time_ns': 1000, 'energy_joules': 1.0, 'ram_rss_bytes': 1024, 'cpu_utilization_pct': 50.0}] * 5
        val = ValidationService.validate_dataset_records(records)
        self.assertTrue(val['is_valid'])

    def test_full_experiment_execution(self):
        dataset = ExperimentService.execute_scientific_experiment(self.experiment)
        self.assertIsNotNone(dataset)
        self.assertEqual(dataset.observations.count(), 24)  # (2 warmup + 10 runs) * 2 libraries
        self.assertTrue(dataset.statistics.exists())
        self.assertTrue(dataset.hypothesis_tests.exists())
        self.assertNotEqual(dataset.checksum_sha256, '')

    def test_dataset_views(self):
        dataset = ExperimentService.execute_scientific_experiment(self.experiment)
        
        res_cat = self.client.get(reverse('experiments:dataset_catalog'))
        self.assertEqual(res_cat.status_code, 200)

        res_detail = self.client.get(reverse('experiments:dataset_detail', args=[dataset.pk]))
        self.assertEqual(res_detail.status_code, 200)

        res_csv = self.client.get(reverse('experiments:dataset_export', args=[dataset.pk, 'csv']))
        self.assertEqual(res_csv.status_code, 200)
