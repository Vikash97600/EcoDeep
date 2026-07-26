from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('apps.authentication.urls')),
    path('libraries/', include('apps.libraries.urls')),
    path('benchmarks/', include('apps.benchmark.urls')),
    path('recommendation/', include('apps.recommendation.urls')),
]
