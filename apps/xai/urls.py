from django.urls import path

from apps.xai import views

app_name = 'xai'

urlpatterns = [
    path('dashboard/', views.XAIDashboardView.as_view(), name='dashboard'),
    path('studio/', views.ExplanationStudioView.as_view(), name='explanation_studio'),
    path('why-not/', views.WhyNotAnalysisView.as_view(), name='why_not_analysis'),
    path('trace/', views.DecisionTraceDetailView.as_view(), name='decision_trace'),
    path('trust/', views.TrustScoreboardView.as_view(), name='trust_scoreboard'),
]
