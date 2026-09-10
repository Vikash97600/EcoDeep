import hashlib

from apps.experiments.models import (
    DatasetObservation,
    ScientificDataset,
    ScientificExperiment,
    StatisticalSummary,
    ValidationReport,
)
from apps.experiments.services.confidence_service import ConfidenceService
from apps.experiments.services.hypothesis_service import HypothesisService
from apps.experiments.services.outlier_service import OutlierService
from apps.experiments.services.statistics_service import StatisticsService
from apps.experiments.services.validation_service import ValidationService


class DatasetService:
    """Manages dataset synthesis, outlier filtration, descriptive summarization, and immutable versioning."""

    @staticmethod
    def generate_dataset_from_experiment(experiment: ScientificExperiment, raw_observations: list) -> ScientificDataset:
        """Processes raw experimental observations, filters outliers, computes stats, and publishes dataset."""
        # 1. Create dataset record
        version_str = f"1.0.{experiment.datasets.count() + 1}"
        dataset = ScientificDataset.objects.create(
            experiment=experiment,
            dataset_name=f"Dataset - {experiment.title}",
            semantic_version=version_str,
            description=f"Generated from empirical experiment '{experiment.title}'",
            total_observations=len(raw_observations)
        )

        # 2. Persist raw observations
        observation_objects = []
        for obs_data in raw_observations:
            obs = DatasetObservation(
                dataset=dataset,
                library=obs_data['library'],
                iteration_number=obs_data['iteration_number'],
                is_warmup=obs_data.get('is_warmup', False),
                execution_time_ns=obs_data['execution_time_ns'],
                execution_time_ms=obs_data['execution_time_ms'],
                cpu_utilization_pct=obs_data['cpu_utilization_pct'],
                ram_rss_bytes=obs_data['ram_rss_bytes'],
                ram_rss_mb=obs_data['ram_rss_mb'],
                energy_joules=obs_data['energy_joules'],
                co2_emissions_g=obs_data['co2_emissions_g'],
                power_watts=obs_data['power_watts']
            )
            observation_objects.append(obs)

        DatasetObservation.objects.bulk_create(observation_objects)

        # 3. Outlier detection per library
        total_outliers = 0
        candidate_libs = experiment.candidate_libraries.all()

        for lib in candidate_libs:
            lib_obs = list(dataset.observations.filter(library=lib, is_warmup=False))
            latencies = [o.execution_time_ms for o in lib_obs]
            
            if experiment.outlier_method == 'IQR':
                outlier_flags = OutlierService.detect_iqr_outliers(latencies)
            elif experiment.outlier_method == 'Z_SCORE':
                outlier_flags = OutlierService.detect_zscore_outliers(latencies)
            else:
                outlier_flags = OutlierService.detect_mad_outliers(latencies)

            for obs_record, is_out in zip(lib_obs, outlier_flags):
                if is_out:
                    obs_record.is_outlier = True
                    obs_record.save(update_fields=['is_outlier'])
                    total_outliers += 1

            # 4. Compute statistical summaries for key metrics
            clean_latencies = [o.execution_time_ms for o in lib_obs if not o.is_outlier]
            clean_energies = [o.energy_joules for o in lib_obs if not o.is_outlier]

            if clean_latencies:
                stats_lat = StatisticsService.compute_descriptive_stats(clean_latencies)
                StatisticalSummary.objects.create(
                    dataset=dataset,
                    library=lib,
                    metric_name='execution_time_ms',
                    **stats_lat
                )

            if clean_energies:
                stats_energy = StatisticsService.compute_descriptive_stats(clean_energies)
                StatisticalSummary.objects.create(
                    dataset=dataset,
                    library=lib,
                    metric_name='energy_joules',
                    **stats_energy
                )

        dataset.total_outliers = total_outliers

        # 5. Validation and Confidence Index
        records_dict = list(dataset.observations.values(
            'execution_time_ns', 'energy_joules', 'ram_rss_bytes', 'cpu_utilization_pct'
        ))
        val_res = ValidationService.validate_dataset_records(records_dict)

        ValidationReport.objects.create(
            dataset=dataset,
            is_valid=val_res['is_valid'],
            passed_rules_count=val_res['passed_rules'],
            failed_rules_count=val_res['failed_rules'],
            validation_details={'violations': val_res['violations']}
        )

        # Average CV across libraries for confidence computation
        summaries = dataset.statistics.all()
        avg_cv = sum(s.coefficient_of_variation for s in summaries) / max(1, summaries.count()) if summaries.exists() else 0.0

        confidence = ConfidenceService.calculate_confidence_index(
            sample_size=experiment.measurement_iterations,
            cv_percent=avg_cv,
            outlier_count=total_outliers,
            total_observations=dataset.total_observations
        )
        quality = ConfidenceService.calculate_data_quality_score(
            passed_rules=val_res['passed_rules'],
            total_rules=val_res['passed_rules'] + val_res['failed_rules']
        )

        dataset.confidence_index = confidence
        dataset.data_quality_score = quality

        # Compute SHA256 checksum for immutability
        dataset_content = f"{dataset.id}-{dataset.dataset_name}-{dataset.total_observations}-{confidence}"
        dataset.checksum_sha256 = hashlib.sha256(dataset_content.encode('utf-8')).hexdigest()
        dataset.save()

        # 6. Run automated pairwise hypothesis tests if 2 or more candidates exist
        lib_list = list(candidate_libs)
        if len(lib_list) >= 2:
            baseline = lib_list[0]
            for target in lib_list[1:]:
                HypothesisService.evaluate_library_pair(dataset, baseline, target, 'execution_time_ms')
                HypothesisService.evaluate_library_pair(dataset, baseline, target, 'energy_joules')

        return dataset
