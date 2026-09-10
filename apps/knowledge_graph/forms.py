from django import forms

from apps.libraries.models import Library


class LibrarySimilarityQueryForm(forms.Form):
    library = forms.ModelChoiceField(
        queryset=Library.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
