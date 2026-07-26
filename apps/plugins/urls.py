from django.urls import path
from apps.plugins import views

app_name = 'plugins'

urlpatterns = [
    path('registry/', views.PluginRegistryListView.as_view(), name='plugin_registry'),
    path('registry/<int:pk>/', views.PluginDetailView.as_view(), name='plugin_detail'),
    path('registry/<int:pk>/toggle/', views.PluginToggleView.as_view(), name='plugin_toggle'),
]
