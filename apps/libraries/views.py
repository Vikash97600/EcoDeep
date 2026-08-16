from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from django.http import HttpResponse

from apps.libraries.models import ProgrammingLanguage, Category, Library, LibraryVersion, SimilarLibraryMapping
from apps.libraries.forms import (
    ProgrammingLanguageForm, CategoryForm, LibraryForm,
    LibraryVersionForm, SimilarLibraryMappingForm, BulkImportForm
)
from apps.libraries.services import BulkDataService
from apps.core.models import AuditLog
from apps.authentication.decorators import researcher_required, admin_required
from django.utils.decorators import method_decorator

class LibraryDashboardView(View):
    """Knowledge base admin dashboard rendering metric summary cards and activity logs."""
    template_name = 'libraries/dashboard.html'

    def get(self, request):
        context = {
            'total_languages': ProgrammingLanguage.objects.count(),
            'total_categories': Category.objects.count(),
            'total_libraries': Library.objects.count(),
            'total_versions': LibraryVersion.objects.count(),
            'total_mappings': SimilarLibraryMapping.objects.count(),
            'recent_libraries': Library.objects.select_related('programming_language', 'category').order_by('-created_at')[:5],
            'recent_mappings': SimilarLibraryMapping.objects.select_related('source_library', 'target_library').order_by('-created_at')[:5],
        }
        return render(request, self.template_name, context)


class LanguageListView(ListView):
    model = ProgrammingLanguage
    template_name = 'libraries/language_list.html'
    context_object_name = 'languages'
    paginate_by = 10


class CategoryListView(ListView):
    model = Category
    template_name = 'libraries/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10


class LibraryListView(ListView):
    model = Library
    template_name = 'libraries/library_list.html'
    context_object_name = 'libraries'
    paginate_by = 12

    def get_queryset(self):
        queryset = Library.objects.select_related('programming_language', 'category').all()
        q = self.request.GET.get('q')
        category_id = self.request.GET.get('category')
        language_id = self.request.GET.get('language')

        if q:
            queryset = queryset.filter(
                Q(library_name__icontains=q) |
                Q(official_name__icontains=q) |
                Q(description__icontains=q)
            )
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if language_id:
            queryset = queryset.filter(programming_language_id=language_id)

        return queryset.order_by('-popularity_score', 'library_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(status='ACTIVE')
        context['languages'] = ProgrammingLanguage.objects.filter(status='ACTIVE')
        context['search_q'] = self.request.GET.get('q', '')
        return context


class LibraryDetailView(DetailView):
    model = Library
    template_name = 'libraries/library_detail.html'
    context_object_name = 'library'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['versions'] = self.object.versions.all()
        context['equivalent_mappings'] = SimilarLibraryMapping.objects.filter(
            Q(source_library=self.object) | Q(target_library=self.object)
        ).select_related('source_library', 'target_library')
        return context


@method_decorator(researcher_required, name='dispatch')
class LibraryCreateView(CreateView):
    model = Library
    form_class = LibraryForm
    template_name = 'libraries/library_form.html'
    success_url = reverse_lazy('libraries:library_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditLog.objects.create(
            user=self.request.user,
            action='LIBRARY_CREATED',
            module='libraries',
            description=f"Created library {self.object.library_name}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        messages.success(self.request, f"Library '{self.object.library_name}' created successfully.")
        return response


@method_decorator(researcher_required, name='dispatch')
class LibraryUpdateView(UpdateView):
    model = Library
    form_class = LibraryForm
    template_name = 'libraries/library_form.html'

    def get_success_url(self):
        return reverse_lazy('libraries:library_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditLog.objects.create(
            user=self.request.user,
            action='LIBRARY_UPDATED',
            module='libraries',
            description=f"Updated library {self.object.library_name}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        messages.success(self.request, f"Library '{self.object.library_name}' updated successfully.")
        return response


class MappingListView(ListView):
    model = SimilarLibraryMapping
    template_name = 'libraries/mapping_list.html'
    context_object_name = 'mappings'
    paginate_by = 25

    def get_queryset(self):
        queryset = SimilarLibraryMapping.objects.select_related('source_library', 'target_library').all()
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(source_library__library_name__icontains=q) |
                Q(target_library__library_name__icontains=q) |
                Q(reason__icontains=q)
            )
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_mappings_count'] = SimilarLibraryMapping.objects.count()
        context['search_q'] = self.request.GET.get('q', '')
        return context


@method_decorator(researcher_required, name='dispatch')
class MappingCreateView(CreateView):
    model = SimilarLibraryMapping
    form_class = SimilarLibraryMappingForm
    template_name = 'libraries/mapping_form.html'
    success_url = reverse_lazy('libraries:mapping_list')

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.verified_by = self.request.user
        else:
            form.instance.verified_by = None
        response = super().form_valid(form)
        messages.success(self.request, f"Equivalence mapping created between '{self.object.source_library.library_name}' and '{self.object.target_library.library_name}'.")
        return response


@method_decorator(researcher_required, name='dispatch')
class BulkImportView(View):
    template_name = 'libraries/bulk_import.html'

    def get(self, request):
        form = BulkImportForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = BulkImportForm(request.POST, request.FILES)
        if form.is_valid():
            imported_count = BulkDataService.import_libraries_csv(request.FILES['file'])
            if imported_count > 0:
                messages.success(request, f"Successfully imported/updated {imported_count} libraries in the catalog!")
            else:
                messages.warning(request, "No valid library records found in the uploaded CSV file. Please check column headers.")
            return redirect('libraries:library_list')
        return render(request, self.template_name, {'form': form})


class ExportDataView(View):
    def get(self, request, format_type='csv'):
        csv_data = BulkDataService.export_libraries_csv()
        response = HttpResponse(csv_data, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="ecodep_libraries_catalog.csv"'
        return response
