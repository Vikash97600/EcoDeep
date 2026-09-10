from django.urls import path

from apps.libraries import views

app_name = 'libraries'

urlpatterns = [
    path('dashboard/', views.LibraryDashboardView.as_view(), name='dashboard'),
    path('languages/', views.LanguageListView.as_view(), name='language_list'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('catalog/', views.LibraryListView.as_view(), name='library_list'),
    path('catalog/add/', views.LibraryCreateView.as_view(), name='library_create'),
    path('catalog/<int:pk>/', views.LibraryDetailView.as_view(), name='library_detail'),
    path('catalog/<int:pk>/edit/', views.LibraryUpdateView.as_view(), name='library_update'),
    path('mappings/', views.MappingListView.as_view(), name='mapping_list'),
    path('mappings/add/', views.MappingCreateView.as_view(), name='mapping_create'),
    path('import/', views.BulkImportView.as_view(), name='bulk_import'),
    path('export/<str:format_type>/', views.ExportDataView.as_view(), name='export_data'),
]
