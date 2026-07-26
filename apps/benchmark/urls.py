from django.urls import path
from apps.benchmark import views

app_name = 'benchmark'

urlpatterns = [
    path('dashboard/', views.BenchmarkDashboardView.as_view(), name='dashboard'),
    path('sessions/', views.SessionListView.as_view(), name='session_list'),
    path('sessions/create/', views.SessionCreateView.as_view(), name='session_create'),
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:pk>/cancel/', views.SessionCancelView.as_view(), name='session_cancel'),
    path('jobs/', views.JobQueueListView.as_view(), name='job_queue'),
]
