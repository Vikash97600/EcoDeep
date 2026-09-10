from django.urls import path

from apps.ai import views

app_name = 'ai'

urlpatterns = [
    path('dashboard/', views.AIPredictionDashboardView.as_view(), name='dashboard'),
    path('predict/', views.PredictSustainabilityView.as_view(), name='predict_sustainability'),
    path('models/', views.ModelRegistryListView.as_view(), name='model_registry'),
    path('models/train/', views.ModelTrainView.as_view(), name='model_train'),
    path('models/<int:pk>/', views.ModelDetailView.as_view(), name='model_detail'),
    path('drift/', views.DriftMonitoringView.as_view(), name='drift_monitor'),
]
