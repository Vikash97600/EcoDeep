from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('admin/', lambda request: redirect('dashboard:admin_workspace')),
    path('auth/', include('apps.authentication.urls')),
    path('libraries/', include('apps.libraries.urls')),
    path('benchmarks/', include('apps.benchmark.urls')),
    path('recommendation/', include('apps.recommendation.urls')),
    path('api/', include('apps.api.urls')),
    path('reports/', include('apps.reports.urls')),
    path('plugins/', include('apps.plugins.urls')),
    path('experiments/', include('apps.experiments.urls')),
    path('', include('apps.dashboard.urls')),
]
