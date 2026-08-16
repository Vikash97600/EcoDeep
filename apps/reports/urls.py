from django.urls import path
from apps.reports import views

app_name = 'reports'

urlpatterns = [
    path('center/', views.ReportsCenterView.as_view(), name='reports_center'),
    path('thesis/generator/', views.ThesisGeneratorStudioView.as_view(), name='thesis_generator'),
    path('ieee/generator/', views.IEEEPaperGeneratorStudioView.as_view(), name='ieee_generator'),
    path('detail/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('artifacts/', views.ArtifactPackageListView.as_view(), name='artifact_packages'),
    path('export/<int:pk>/<str:format_choice>/', views.ReportExportDocumentView.as_view(), name='export_document'),
    path('export/<str:report_type>/<str:format_type>/', views.ReportExportView.as_view(), name='export_csv'),
]
