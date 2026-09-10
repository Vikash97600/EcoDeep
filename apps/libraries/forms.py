from django import forms
from django.core.exceptions import ValidationError

from apps.libraries.models import (
    Category,
    Library,
    LibraryVersion,
    ProgrammingLanguage,
    SimilarLibraryMapping,
)


class ProgrammingLanguageForm(forms.ModelForm):
    class Meta:
        model = ProgrammingLanguage
        fields = ['language_name', 'slug', 'description', 'logo', 'status']
        widgets = {
            'language_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. python'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name', 'slug', 'description', 'icon', 'status']
        widgets = {
            'category_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Data Serialization'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. data-serialization'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-solid fa-boxes'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class LibraryForm(forms.ModelForm):
    class Meta:
        model = Library
        fields = [
            'library_name', 'official_name', 'programming_language', 'category',
            'description', 'package_manager', 'repository_url', 'documentation_url',
            'homepage_url', 'current_version', 'license', 'maintainer',
            'popularity_score', 'downloads', 'status'
        ]
        widgets = {
            'library_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. orjson'}),
            'official_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. orjson Fast Python JSON Library'}),
            'programming_language': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'package_manager': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PyPI'}),
            'repository_url': forms.URLInput(attrs={'class': 'form-control'}),
            'documentation_url': forms.URLInput(attrs={'class': 'form-control'}),
            'homepage_url': forms.URLInput(attrs={'class': 'form-control'}),
            'current_version': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '3.9.1'}),
            'license': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'MIT'}),
            'maintainer': forms.TextInput(attrs={'class': 'form-control'}),
            'popularity_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'downloads': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure optional fields don't block form submission
        optional_fields = [
            'official_name', 'description', 'package_manager', 'repository_url',
            'documentation_url', 'homepage_url', 'current_version', 'license',
            'maintainer', 'popularity_score', 'downloads', 'status'
        ]
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()
        lib_name = cleaned_data.get('library_name')
        lang = cleaned_data.get('programming_language')
        official_name = cleaned_data.get('official_name')

        if lib_name:
            if not official_name:
                cleaned_data['official_name'] = lib_name

            if lang:
                qs = Library.objects.filter(library_name__iexact=lib_name, programming_language=lang)
                if self.instance and self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise ValidationError(f"A library named '{lib_name}' for language '{lang.language_name}' already exists.")

        return cleaned_data


class LibraryVersionForm(forms.ModelForm):
    class Meta:
        model = LibraryVersion
        fields = ['library', 'version_number', 'release_date', 'release_notes', 'supported_python_version', 'status']
        widgets = {
            'library': forms.Select(attrs={'class': 'form-select'}),
            'version_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 3.9.1'}),
            'release_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'release_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'supported_python_version': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '>=3.8'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class SimilarLibraryMappingForm(forms.ModelForm):
    class Meta:
        model = SimilarLibraryMapping
        fields = ['source_library', 'target_library', 'similarity_type', 'similarity_score', 'reason', 'status']
        widgets = {
            'source_library': forms.Select(attrs={'class': 'form-select'}),
            'target_library': forms.Select(attrs={'class': 'form-select'}),
            'similarity_type': forms.Select(attrs={'class': 'form-select'}),
            'similarity_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.00', 'max': '1.00'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Explain why these packages are functionally equivalent'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'similarity_score' in self.fields:
            self.fields['similarity_score'].required = False
            self.fields['similarity_score'].initial = 0.85
        if 'reason' in self.fields:
            self.fields['reason'].required = False
        if 'status' in self.fields:
            self.fields['status'].required = False

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('source_library')
        target = cleaned_data.get('target_library')
        score = cleaned_data.get('similarity_score')
        reason = cleaned_data.get('reason')

        if source and target:
            if source == target:
                raise ValidationError("Source and target libraries cannot be the same package.")

            # Check for existing duplicate mapping
            qs = SimilarLibraryMapping.objects.filter(source_library=source, target_library=target)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"An equivalence mapping between '{source.library_name}' and '{target.library_name}' already exists.")

            if not score:
                cleaned_data['similarity_score'] = 0.85

            if not reason:
                cleaned_data['reason'] = f"Functional alternative and green replacement mapping between {source.library_name} and {target.library_name}."

        return cleaned_data


class BulkImportForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}))
