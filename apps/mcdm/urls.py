from django.urls import path

from apps.mcdm import views

app_name = 'mcdm'

urlpatterns = [
    path('dashboard/', views.MCDMDashboardView.as_view(), name='dashboard'),
    path('ranking/studio/', views.MCDMRankingStudioView.as_view(), name='ranking_studio'),
    path('evaluation/<int:pk>/', views.MCDMEvaluationDetailView.as_view(), name='evaluation_detail'),
    path('profiles/', views.WeightProfileListView.as_view(), name='weight_profiles'),
    path('profiles/create/', views.WeightProfileCreateView.as_view(), name='weight_profile_create'),
    path('ahp/calculator/', views.AHPMatrixCalculatorView.as_view(), name='ahp_calculator'),
    path('sensitivity/', views.SensitivityAnalysisView.as_view(), name='sensitivity_analysis'),
]
