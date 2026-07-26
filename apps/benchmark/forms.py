from django import forms
from apps.benchmark.models import (
    BenchmarkSession, BenchmarkTask, BenchmarkDataset,
    DatasetVersion, BenchmarkProfile, DatasetTypeChoices
)
from apps.libraries.models import Category, LibraryVersion
from apps.benchmark.validators import validate_dataset_file_extension

class BenchmarkSessionForm(forms.Form):
    session_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. JSON Parsers 10MB Benchmark Run'}))
    category = forms.ModelChoiceField(queryset=Category.objects.filter(status='ACTIVE'), widget=forms.Select(attrs={'class': 'form-select'}))
    task = forms.ModelChoiceField(queryset=BenchmarkTask.objects.filter(status='ACTIVE'), widget=forms.Select(attrs={'class': 'form-select'}))
    library_versions = forms.ModelMultipleChoiceField(
        queryset=LibraryVersion.objects.filter(status='ACTIVE').select_related('library'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '6'}),
        help_text="Hold Ctrl / Cmd to select candidate library versions within the chosen category."
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Benchmark execution notes'}))

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        task = cleaned_data.get('task')
        versions = cleaned_data.get('library_versions')

        if task and category and task.category != category:
            self.add_error('task', f"Selected task '{task}' belongs to category '{task.category}', which does not match selected category '{category}'.")

        if versions and category:
            invalid_versions = [v for v in versions if v.library.category != category]
            if invalid_versions:
                self.add_error('library_versions', f"All selected library versions must belong to category '{category}'. Invalid versions: {', '.join([str(v) for v in invalid_versions])}")

        return cleaned_data


class BenchmarkTaskForm(forms.ModelForm):
    class Meta:
        model = BenchmarkTask
        fields = ['task_name', 'category', 'dataset', 'description', 'expected_output', 'iterations', 'warmup_runs', 'timeout_seconds', 'status']
        widgets = {
            'task_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. JSON Deserialization 10MB'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'dataset': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'expected_output': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. dict / sha256'}),
            'iterations': forms.NumberInput(attrs={'class': 'form-control', 'value': 50}),
            'warmup_runs': forms.NumberInput(attrs={'class': 'form-control', 'value': 5}),
            'timeout_seconds': forms.NumberInput(attrs={'class': 'form-control', 'value': 30}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class BenchmarkDatasetForm(forms.ModelForm):
    file_path = forms.FileField(validators=[validate_dataset_file_extension], widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = BenchmarkDataset
        fields = ['dataset_name', 'dataset_category', 'dataset_type', 'description', 'file_path', 'status']
        widgets = {
            'dataset_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 10MB Synthetic JSON'}),
            'dataset_category': forms.Select(attrs={'class': 'form-select'}),
            'dataset_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class DatasetGeneratorForm(forms.Form):
    dataset_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Synthetic JSON 50K Records'}))
    category = forms.ModelChoiceField(queryset=Category.objects.filter(status='ACTIVE'), widget=forms.Select(attrs={'class': 'form-select'}))
    dataset_type = forms.ChoiceField(choices=[('JSON', 'JSON Document Payload'), ('CSV', 'Comma Separated Values')], widget=forms.Select(attrs={'class': 'form-select'}))
    record_count = forms.IntegerField(initial=10000, min_value=100, max_value=100000, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    random_seed = forms.IntegerField(initial=42, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))


class BenchmarkProfileForm(forms.ModelForm):
    class Meta:
        model = BenchmarkProfile
        fields = ['profile_name', 'description', 'iterations', 'warmup_runs', 'timeout_seconds', 'random_seed']
        widgets = {
            'profile_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Standard Research Profile'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'iterations': forms.NumberInput(attrs={'class': 'form-control'}),
            'warmup_runs': forms.NumberInput(attrs={'class': 'form-control'}),
            'timeout_seconds': forms.NumberInput(attrs={'class': 'form-control'}),
            'random_seed': forms.NumberInput(attrs={'class': 'form-control'}),
        }
