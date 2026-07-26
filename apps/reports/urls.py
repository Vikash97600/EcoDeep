from django.urls import path
from apps.reports import views

app_name = 'reports'

urlpatterns = [
    path('center/', views.ReportsCenterView.as_view(), name='reports_center'),
    path('export/<str:report_type>/<str:format_type>/', views.ReportExportView.as_view(), name='report_export'),
]
