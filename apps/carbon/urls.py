from django.urls import path

from apps.carbon import views

app_name = 'carbon'

urlpatterns = [
    path('dashboard/', views.CarbonIntelligenceDashboardView.as_view(), name='dashboard'),
    path('regions/', views.RegionalGridListView.as_view(), name='regional_grids'),
    path('compare/', views.CarbonComparisonStudioView.as_view(), name='comparison_studio'),
    path('savings/', views.CarbonSavingsCalculatorView.as_view(), name='savings_calculator'),
    path('forecast/', views.CarbonForecastView.as_view(), name='carbon_forecast'),
]
