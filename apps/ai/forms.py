from django import forms
from apps.ai.models import PredictionTargetChoices, ModelAlgorithmChoices
from apps.libraries.models import Library

class SustainabilityPredictionForm(forms.Form):
    library = forms.ModelChoiceField(
        queryset=Library.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    target_metric = forms.ChoiceField(
        choices=PredictionTargetChoices.choices,
        initial=PredictionTargetChoices.GREEN_SCORE,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ModelTrainingForm(forms.Form):
    algorithm = forms.ChoiceField(
        choices=ModelAlgorithmChoices.choices,
        initial=ModelAlgorithmChoices.RIDGE_REGRESSION,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    target_metric = forms.ChoiceField(
        choices=PredictionTargetChoices.choices,
        initial=PredictionTargetChoices.GREEN_SCORE,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
