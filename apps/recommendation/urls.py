from django.urls import path
from apps.recommendation import views

app_name = 'recommendation'

urlpatterns = [
    path('greenscore/dashboard/', views.GreenScoreDashboardView.as_view(), name='greenscore_dashboard'),
    path('greenscore/calculate/<int:session_id>/', views.CalculateGreenScoreView.as_view(), name='calculate_greenscore'),
    path('greenscore/profiles/', views.WeightProfileListView.as_view(), name='weight_profiles'),
    path('greenscore/profiles/create/', views.WeightProfileCreateView.as_view(), name='profile_create'),
    path('greenscore/rankings/', views.RankingTableView.as_view(), name='ranking_table'),
]
