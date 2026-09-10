from django.urls import path

from apps.recommendation import views

app_name = 'recommendation'

urlpatterns = [
    # Green Score Engine URLs
    path('greenscore/dashboard/', views.GreenScoreDashboardView.as_view(), name='greenscore_dashboard'),
    path('greenscore/calculate/<int:session_id>/', views.CalculateGreenScoreView.as_view(), name='calculate_greenscore'),
    path('greenscore/profiles/', views.WeightProfileListView.as_view(), name='weight_profiles'),
    path('greenscore/profiles/create/', views.WeightProfileCreateView.as_view(), name='profile_create'),
    path('greenscore/rankings/', views.RankingTableView.as_view(), name='ranking_table'),

    # Intelligent Recommendation Engine URLs
    path('recommend/query/', views.RecommendationQueryView.as_view(), name='recommend_query'),
    path('recommend/<int:pk>/', views.RecommendationDetailView.as_view(), name='recommend_detail'),
    path('recommend/history/', views.RecommendationHistoryListView.as_view(), name='recommend_history'),
    path('api/v1/recommend/', views.APIRecommendationQueryView.as_view(), name='api_recommend_query'),
]
