from django import forms

from apps.benchmark.models import (
    BenchmarkDataset,
    BenchmarkProfile,
    BenchmarkTask,
)
from apps.benchmark.validators import validate_dataset_file_extension
from apps.libraries.models import Category, LibraryVersion


class BenchmarkSessionForm(forms.Form):
    session_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. JSON Parsers 10MB Benchmark Run'}))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    task = forms.ModelChoiceField(queryset=BenchmarkTask.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    library_versions = forms.ModelMultipleChoiceField(
        queryset=LibraryVersion.objects.all().select_related('library'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '6'}),
        help_text="Hold Ctrl / Cmd to select candidate library versions."
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Benchmark execution notes'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['task'].queryset = BenchmarkTask.objects.all().select_related('category')
        
        # Ensure all existing libraries have at least one active LibraryVersion
        from apps.libraries.models import Library
        for lib in Library.objects.all():
            LibraryVersion.objects.get_or_create(
                library=lib,
                version_number=lib.current_version or '1.0.0',
                defaults={'status': 'ACTIVE', 'supported_python_version': '>=3.8'}
            )
        self.fields['library_versions'].queryset = LibraryVersion.objects.all().select_related('library')

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
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Workload operation details'}),
            'expected_output': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. dict / sha256'}),
            'iterations': forms.NumberInput(attrs={'class': 'form-control', 'value': 50}),
            'warmup_runs': forms.NumberInput(attrs={'class': 'form-control', 'value': 5}),
            'timeout_seconds': forms.NumberInput(attrs={'class': 'form-control', 'value': 30}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['dataset'].queryset = BenchmarkDataset.objects.all()
        if 'dataset' in self.fields:
            self.fields['dataset'].required = False
        if 'description' in self.fields:
            self.fields['description'].required = False
        if 'expected_output' in self.fields:
            self.fields['expected_output'].required = False
            self.fields['expected_output'].initial = 'dict / sha256'
        if 'status' in self.fields:
            self.fields['status'].required = False
            self.fields['status'].initial = 'ACTIVE'

    def clean(self):
        cleaned_data = super().clean()
        task_name = cleaned_data.get('task_name')
        cat = cleaned_data.get('category')
        dataset = cleaned_data.get('dataset')
        desc = cleaned_data.get('description')
        expected_out = cleaned_data.get('expected_output')

        if not desc and task_name:
            cleaned_data['description'] = f"Standard benchmark workload task: {task_name}"

        if not expected_out:
            cleaned_data['expected_output'] = 'dict / sha256'

        if not dataset and cat:
            dataset, _ = BenchmarkDataset.objects.get_or_create(
                dataset_name=f"Default Synthetic Dataset ({cat.category_name})",
                dataset_category=cat,
                defaults={
                    'dataset_type': 'JSON',
                    'description': f"Default dataset for {cat.category_name} benchmarks",
                    'dataset_size_bytes': 1024,
                    'status': 'ACTIVE'
                }
            )
            cleaned_data['dataset'] = dataset

        return cleaned_data


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
