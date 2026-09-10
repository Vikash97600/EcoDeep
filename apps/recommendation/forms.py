from django import forms

from apps.benchmark.models import BenchmarkTask
from apps.libraries.models import Library
from apps.recommendation.models import RecommendationProfileChoices, WeightProfile


class WeightProfileForm(forms.ModelForm):
    class Meta:
        model = WeightProfile
        fields = ['profile_name', 'description', 'weight_execution_time', 'weight_cpu_usage', 'weight_peak_memory', 'weight_energy', 'weight_co2', 'is_default']
        widgets = {
            'profile_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Energy First Profile'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'weight_execution_time': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05'}),
            'weight_cpu_usage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05'}),
            'weight_peak_memory': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05'}),
            'weight_energy': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05'}),
            'weight_co2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        w1 = float(cleaned_data.get('weight_execution_time', 0))
        w2 = float(cleaned_data.get('weight_cpu_usage', 0))
        w3 = float(cleaned_data.get('weight_peak_memory', 0))
        w4 = float(cleaned_data.get('weight_energy', 0))
        w5 = float(cleaned_data.get('weight_co2', 0))

        total_weight = round(w1 + w2 + w3 + w4 + w5, 2)
        if total_weight != 1.00:
            raise forms.ValidationError(f"Total weights must sum to exactly 1.00 (100%). Current sum: {total_weight}")

        return cleaned_data


class RecommendationQueryForm(forms.Form):
    target_library = forms.ModelChoiceField(
        queryset=Library.objects.filter(status='ACTIVE'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Target Software Library"
    )
    task = forms.ModelChoiceField(
        queryset=BenchmarkTask.objects.filter(status='ACTIVE'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Workload Task Benchmark"
    )
    profile_type = forms.ChoiceField(
        choices=RecommendationProfileChoices.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial=RecommendationProfileChoices.BEST_OVERALL,
        label="Multi-Objective Optimization Profile"
    )
