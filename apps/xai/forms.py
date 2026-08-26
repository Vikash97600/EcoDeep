from django import forms
from apps.libraries.models import Library
from apps.xai.models import PersonaTypeChoices

class LibraryCategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        cat_name = obj.category.category_name if obj.category else 'General'
        return f"{obj.library_name} ({cat_name})"


class ExplanationQueryForm(forms.Form):
    library = LibraryCategoryChoiceField(
        queryset=Library.objects.select_related('category').all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    persona = forms.ChoiceField(
        choices=PersonaTypeChoices.choices,
        initial=PersonaTypeChoices.DEVELOPER,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class WhyNotQueryForm(forms.Form):
    unrecommended_library = LibraryCategoryChoiceField(
        queryset=Library.objects.select_related('category').all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    winning_library = LibraryCategoryChoiceField(
        queryset=Library.objects.select_related('category').all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
