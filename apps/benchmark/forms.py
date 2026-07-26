from django import forms
from apps.benchmark.models import BenchmarkSession, BenchmarkTask, BenchmarkDataset
from apps.libraries.models import Category, LibraryVersion

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
