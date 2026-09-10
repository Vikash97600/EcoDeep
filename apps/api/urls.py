from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from apps.api import views

app_name = 'api'

router = DefaultRouter()
router.register(r'libraries', views.LibraryViewSet, basename='library')
router.register(r'library-versions', views.LibraryVersionViewSet, basename='libraryversion')
router.register(r'tasks', views.BenchmarkTaskViewSet, basename='task')
router.register(r'sessions', views.BenchmarkSessionViewSet, basename='session')
router.register(r'results', views.BenchmarkResultViewSet, basename='result')
router.register(r'greenscores', views.GreenScoreViewSet, basename='greenscore')
router.register(r'recommendations', views.RecommendationViewSet, basename='recommendation')

urlpatterns = [
    # API Authentication & Token Endpoint
    path('v1/auth/token/', obtain_auth_token, name='api_token'),

    # Observability Endpoints
    path('v1/health/', views.HealthCheckView.as_view(), name='api_health'),
    path('v1/metrics/', views.MetricsView.as_view(), name='api_metrics'),

    # REST Router Endpoints
    path('v1/', include(router.urls)),
]
