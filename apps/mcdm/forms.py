from django import forms

from apps.libraries.models import Category
from apps.mcdm.models import MCDMMethodChoices, MCDMWeightProfile


class MCDMRankingQueryForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    weight_profile = forms.ModelChoiceField(
        queryset=MCDMWeightProfile.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    mcdm_method = forms.ChoiceField(
        choices=MCDMMethodChoices.choices,
        initial=MCDMMethodChoices.TOPSIS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class WeightProfileForm(forms.ModelForm):
    class Meta:
        model = MCDMWeightProfile
        fields = [
            'profile_name', 'profile_type', 'weight_energy', 'weight_execution_time',
            'weight_cpu', 'weight_memory', 'weight_co2', 'is_default', 'notes'
        ]
        widgets = {
            'profile_name': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_type': forms.Select(attrs={'class': 'form-select'}),
            'weight_energy': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05', 'min': '0', 'max': '1'}),
            'weight_execution_time': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05', 'min': '0', 'max': '1'}),
            'weight_cpu': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05', 'min': '0', 'max': '1'}),
            'weight_memory': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05', 'min': '0', 'max': '1'}),
            'weight_co2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.05', 'min': '0', 'max': '1'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
        }
