from django.urls import path
from apps.experiments import views

app_name = 'experiments'

urlpatterns = [
    path('', views.ExperimentListView.as_view(), name='experiment_list'),
    path('create/', views.ExperimentCreateView.as_view(), name='experiment_create'),
    path('<int:pk>/', views.ExperimentDetailView.as_view(), name='experiment_detail'),
    path('<int:pk>/execute/', views.ExperimentExecuteView.as_view(), name='experiment_execute'),
    path('datasets/', views.DatasetCatalogView.as_view(), name='dataset_catalog'),
    path('datasets/<int:pk>/', views.DatasetDetailView.as_view(), name='dataset_detail'),
    path('datasets/<int:pk>/export/<str:export_format>/', views.DatasetExportView.as_view(), name='dataset_export'),
    path('datasets/<int:pk>/report/', views.StatisticalReportView.as_view(), name='statistical_report'),
]
