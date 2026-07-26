from django.urls import path
from apps.benchmark import views

app_name = 'benchmark'

urlpatterns = [
    # Benchmark Core Engine
    path('dashboard/', views.BenchmarkDashboardView.as_view(), name='dashboard'),
    path('sessions/', views.SessionListView.as_view(), name='session_list'),
    path('sessions/create/', views.SessionCreateView.as_view(), name='session_create'),
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:pk>/cancel/', views.SessionCancelView.as_view(), name='session_cancel'),
    path('jobs/', views.JobQueueListView.as_view(), name='job_queue'),

    # Benchmark Runner URLs
    path('runner/dashboard/', views.RunnerDashboardView.as_view(), name='runner_dashboard'),
    path('runner/trigger/<int:session_id>/', views.TriggerRunnerView.as_view(), name='trigger_runner'),
    path('runner/jobs/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),

    # Execution Time Measurement URLs
    path('time/monitor/<int:result_id>/', views.TimeMonitorView.as_view(), name='time_monitor'),
    path('time/samples/<int:result_id>/', views.TimeSamplesView.as_view(), name='time_samples'),
    path('time/export/<int:result_id>/<str:format_type>/', views.TimeExportView.as_view(), name='time_export'),

    # CPU & Memory Resource Telemetry URLs
    path('resources/cpu/<int:result_id>/', views.CpuMonitorView.as_view(), name='cpu_monitor'),
    path('resources/memory/<int:result_id>/', views.MemoryMonitorView.as_view(), name='memory_monitor'),
    path('resources/export/<int:result_id>/<str:resource_type>/', views.ResourceExportView.as_view(), name='resource_export'),

    # Energy & Carbon Emissions Telemetry URLs
    path('telemetry/energy/<int:result_id>/', views.EnergyMonitorView.as_view(), name='energy_monitor'),
    path('telemetry/co2/<int:result_id>/', views.Co2MonitorView.as_view(), name='co2_monitor'),
    path('telemetry/export/<int:result_id>/energy/', views.EnergyExportView.as_view(), name='energy_export'),

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
