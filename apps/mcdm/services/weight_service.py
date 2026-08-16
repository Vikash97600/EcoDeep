from typing import Dict
from apps.mcdm.models import MCDMWeightProfile, ProfileTypeChoices

class WeightService:
    """Manages MCDM weight profiles, criteria normalization, and profile presets."""

    @staticmethod
    def get_or_create_default_profiles():
        """Ensures standard research weight profiles exist."""
        profiles = [
            {
                'profile_name': 'Standard Balanced Profile',
                'profile_type': ProfileTypeChoices.BALANCED,
                'weight_energy': 0.35,
                'weight_execution_time': 0.25,
                'weight_cpu': 0.15,
                'weight_memory': 0.15,
                'weight_co2': 0.10,
                'is_default': True
            },
            {
                'profile_name': 'Energy-First Green Profile',
                'profile_type': ProfileTypeChoices.ENERGY_FOCUSED,
                'weight_energy': 0.50,
                'weight_execution_time': 0.15,
                'weight_cpu': 0.15,
                'weight_memory': 0.10,
                'weight_co2': 0.10,
                'is_default': False
            },
            {
                'profile_name': 'High-Throughput Performance Profile',
                'profile_type': ProfileTypeChoices.PERFORMANCE_FOCUSED,
                'weight_energy': 0.15,
                'weight_execution_time': 0.50,
                'weight_cpu': 0.15,
                'weight_memory': 0.15,
                'weight_co2': 0.05,
                'is_default': False
            },
            {
                'profile_name': 'Memory-Constrained Edge Profile',
                'profile_type': ProfileTypeChoices.MEMORY_FOCUSED,
                'weight_energy': 0.20,
                'weight_execution_time': 0.15,
                'weight_cpu': 0.15,
                'weight_memory': 0.45,
                'weight_co2': 0.05,
                'is_default': False
            },
            {
                'profile_name': 'Zero-Carbon Profile',
                'profile_type': ProfileTypeChoices.CARBON_NEUTRAL,
                'weight_energy': 0.30,
                'weight_execution_time': 0.10,
                'weight_cpu': 0.10,
                'weight_memory': 0.10,
                'weight_co2': 0.40,
                'is_default': False
            }
        ]

        for p in profiles:
            MCDMWeightProfile.objects.get_or_create(
                profile_name=p['profile_name'],
                defaults=p
            )

    @staticmethod
    def get_normalized_weights(profile: MCDMWeightProfile) -> Dict[str, float]:
        """Returns criteria weights normalized strictly to sum to 1.0."""
        raw = {
            'energy_joules': profile.weight_energy,
            'execution_time_ms': profile.weight_execution_time,
            'cpu_utilization_pct': profile.weight_cpu,
            'ram_rss_mb': profile.weight_memory,
            'co2_emissions_g': profile.weight_co2
        }
        total = sum(raw.values())
        if total == 0:
            total = 1.0
        return {k: round(v / total, 4) for k, v in raw.items()}
