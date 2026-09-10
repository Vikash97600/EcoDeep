from django import forms

from apps.carbon.models import RegionalGridCarbonFactor
from apps.libraries.models import Library


class CarbonComparisonForm(forms.Form):
    library_a = forms.ModelChoiceField(
        queryset=Library.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    library_b = forms.ModelChoiceField(
        queryset=Library.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    regional_grid = forms.ModelChoiceField(
        queryset=RegionalGridCarbonFactor.objects.filter(status='ACTIVE'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class CarbonSavingsCalculatorForm(forms.Form):
    source_library = forms.ModelChoiceField(
        queryset=Library.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    target_library = forms.ModelChoiceField(
        queryset=Library.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    regional_grid = forms.ModelChoiceField(
        queryset=RegionalGridCarbonFactor.objects.filter(status='ACTIVE'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    annual_requests = forms.IntegerField(
        initial=10000000,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1000000', 'min': '1000'})
    )
