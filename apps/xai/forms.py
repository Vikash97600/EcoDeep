from django import forms
from apps.libraries.models import Library
from apps.xai.models import PersonaTypeChoices

class ExplanationQueryForm(forms.Form):
    library = forms.ModelChoiceField(
        queryset=Library.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    persona = forms.ChoiceField(
        choices=PersonaTypeChoices.choices,
        initial=PersonaTypeChoices.DEVELOPER,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class WhyNotQueryForm(forms.Form):
    unrecommended_library = forms.ModelChoiceField(
        queryset=Library.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    winning_library = forms.ModelChoiceField(
        queryset=Library.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
