from django.urls import path
from apps.dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.WorkspaceRedirectView.as_view(), name='index'),
    path('workspace/admin/', views.AdminWorkspaceView.as_view(), name='admin_workspace'),
    path('researcher/', views.ResearcherWorkspaceView.as_view(), name='researcher_workspace'),
    path('developer/', views.DeveloperWorkspaceView.as_view(), name='developer_workspace'),
    path('analytics/', views.AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    path('comparison-studio/', views.ComparisonStudioView.as_view(), name='comparison_studio'),
]
