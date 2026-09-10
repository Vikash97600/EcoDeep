import hashlib

from apps.libraries.models import Library
from apps.xai.models import DecisionTraceAudit


class TraceabilityService:
    """Builds cryptographic decision lineage audits tracking inputs from physical telemetry to recommendations."""

    @staticmethod
    def create_decision_trace(
        library: Library,
        benchmark_runs_count: int = 10,
        weight_profile_name: str = "Standard Balanced Profile",
        mcdm_solver_used: str = "TOPSIS",
        carbon_grid_code: str = "us-east-1",
        lineage_metadata: dict | None = None
    ) -> DecisionTraceAudit:
        """Constructs audit trail with a SHA256 cryptographic fingerprint."""
        if not lineage_metadata:
            lineage_metadata = {
                'library_version': library.current_version,
                'category_id': library.category.id if library.category else 1,
                'measurement_subsystems': ['RAPL_Energy', 'perf_counter_ns', 'psutil_rss'],
                'mcdm_criteria_count': 5
            }

        hash_payload = f"{library.id}-{library.library_name}-{benchmark_runs_count}-{weight_profile_name}-{mcdm_solver_used}-{carbon_grid_code}"
        trace_hash = hashlib.sha256(hash_payload.encode('utf-8')).hexdigest()

        return DecisionTraceAudit.objects.create(
            library=library,
            benchmark_runs_count=benchmark_runs_count,
            weight_profile_used=weight_profile_name,
            mcdm_solver_used=mcdm_solver_used,
            carbon_grid_used=carbon_grid_code,
            trace_hash_sha256=trace_hash,
            lineage_metadata=lineage_metadata
        )
