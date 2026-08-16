from django import forms
from apps.libraries.models import Category

class ThesisGeneratorForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    author_name = forms.CharField(
        initial="Vikash Kumar",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional Custom Dissertation Title'})
    )


class IEEEPaperGeneratorForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    author_name = forms.CharField(
        initial="Vikash Kumar",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional Custom Conference Paper Title'})
    )
