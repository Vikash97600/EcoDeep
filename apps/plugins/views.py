from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.authentication.decorators import admin_required
from apps.plugins.models import PluginManifest
from apps.plugins.services.plugin_registry_service import PluginRegistryService


class PluginRegistryListView(ListView):
    model = PluginManifest
    template_name = 'plugins/plugin_registry.html'
    context_object_name = 'plugins'


class PluginDetailView(DetailView):
    model = PluginManifest
    template_name = 'plugins/plugin_detail.html'
    context_object_name = 'plugin'


@method_decorator(admin_required, name='dispatch')
class PluginToggleView(View):
    def post(self, request, pk):
        plugin = get_object_or_404(PluginManifest, pk=pk)
        new_status = plugin.status != 'ACTIVE'
        PluginRegistryService.toggle_plugin_status(plugin.plugin_id, enable=new_status)
        status_text = 'Enabled' if new_status else 'Disabled'
        messages.success(request, f"Plugin '{plugin.name}' has been {status_text}.")
        return redirect('plugins:plugin_detail', pk=pk)
