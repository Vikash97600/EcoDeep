from django import forms
from apps.experiments.models import ScientificExperiment

class ScientificExperimentForm(forms.ModelForm):
    class Meta:
        model = ScientificExperiment
        fields = [
            'title', 'research_question', 'null_hypothesis', 'alternative_hypothesis',
            'benchmark_task', 'candidate_libraries', 'warmup_iterations',
            'measurement_iterations', 'cooldown_seconds', 'random_seed',
            'outlier_method', 'alpha_threshold'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. JSON Parsing Efficiency Comparison'}),
            'research_question': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'null_hypothesis': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'alternative_hypothesis': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'benchmark_task': forms.Select(attrs={'class': 'form-select'}),
            'candidate_libraries': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'warmup_iterations': forms.NumberInput(attrs={'class': 'form-control'}),
            'measurement_iterations': forms.NumberInput(attrs={'class': 'form-control'}),
            'cooldown_seconds': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'random_seed': forms.NumberInput(attrs={'class': 'form-control'}),
            'outlier_method': forms.Select(attrs={'class': 'form-select'}),
            'alpha_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
