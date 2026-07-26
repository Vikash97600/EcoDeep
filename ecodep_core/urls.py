from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib import messages

def admin_login_redirect(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if request.user.is_superuser or (profile and profile.role and profile.role.role_name == 'ADMIN'):
            return redirect('dashboard:admin_workspace')
        elif profile and profile.role and profile.role.role_name == 'RESEARCHER':
            return redirect('dashboard:researcher_workspace')
        return redirect('dashboard:developer_workspace')
    return redirect('authentication:login')

urlpatterns = [
    path('admin/login/', admin_login_redirect),
    path('admin/', admin.site.urls),
    path('auth/', include('apps.authentication.urls')),
    path('libraries/', include('apps.libraries.urls')),
    path('benchmarks/', include('apps.benchmark.urls')),
    path('recommendation/', include('apps.recommendation.urls')),
    path('api/', include('apps.api.urls')),
    path('reports/', include('apps.reports.urls')),
    path('plugins/', include('apps.plugins.urls')),
    path('', include('apps.dashboard.urls')),
]
