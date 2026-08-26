from django import forms
from apps.ai.models import PredictionTargetChoices, ModelAlgorithmChoices
from apps.libraries.models import Library

class LibraryCategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        lang = obj.programming_language.language_name if obj.programming_language else 'Python'
        cat_name = obj.category.category_name if obj.category else 'General'
        return f"{obj.library_name} ({lang} - {cat_name})"


class SustainabilityPredictionForm(forms.Form):
    library = LibraryCategoryChoiceField(
        queryset=Library.objects.select_related('programming_language', 'category').all(),
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
