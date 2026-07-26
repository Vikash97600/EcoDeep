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

    # Task Management URLs
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),

    # Dataset Management URLs
    path('datasets/', views.DatasetListView.as_view(), name='dataset_list'),
    path('datasets/create/', views.DatasetCreateView.as_view(), name='dataset_create'),
    path('datasets/generate/', views.DatasetGeneratorView.as_view(), name='dataset_generate'),
    path('datasets/<int:pk>/preview/', views.DatasetPreviewView.as_view(), name='dataset_preview'),

    # Experiment Profiles
    path('profiles/', views.ProfileListView.as_view(), name='profile_list'),
]
