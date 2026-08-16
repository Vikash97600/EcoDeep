from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.utils.decorators import method_decorator
from apps.authentication.decorators import researcher_required, admin_required
from apps.knowledge_graph.models import (
    KnowledgeGraphNode, KnowledgeGraphEdge, SimilarityScore, GraphSnapshot
)
from apps.knowledge_graph.forms import LibrarySimilarityQueryForm
from apps.knowledge_graph.services.graph_builder_service import GraphBuilderService
from apps.knowledge_graph.services.graph_query_service import GraphQueryService
from apps.libraries.models import Library

class KnowledgeGraphExplorerView(View):
    template_name = 'knowledge_graph/graph_explorer.html'

    def get(self, request):
        nodes = KnowledgeGraphNode.objects.all()[:30]
        edges = KnowledgeGraphEdge.objects.select_related('source_node', 'target_node')[:50]
        context = {
            'total_nodes': KnowledgeGraphNode.objects.count(),
            'total_edges': KnowledgeGraphEdge.objects.count(),
            'nodes': nodes,
            'edges': edges,
            'recent_snapshots': GraphSnapshot.objects.all()[:3]
        }
        return render(request, self.template_name, context)


class SimilarLibrariesDiscoveryView(View):
    template_name = 'knowledge_graph/similarity_discovery.html'

    def get(self, request):
        form = LibrarySimilarityQueryForm()
        lib_id = request.GET.get('library')
        alternatives = []
        selected_library = None

        if lib_id:
            selected_library = get_object_or_404(Library, pk=lib_id)
            form = LibrarySimilarityQueryForm(initial={'library': selected_library})
            alternatives = GraphQueryService.find_alternative_libraries(selected_library)

        context = {
            'form': form,
            'selected_library': selected_library,
            'alternatives': alternatives,
            'recent_scores': SimilarityScore.objects.select_related('source_library', 'target_library')[:10]
        }
        return render(request, self.template_name, context)


class RelationshipListView(ListView):
    model = KnowledgeGraphEdge
    template_name = 'knowledge_graph/relationship_list.html'
    context_object_name = 'relationships'
    paginate_by = 25


class GraphAnalyticsView(View):
    template_name = 'knowledge_graph/graph_analytics.html'

    def get(self, request):
        analytics = GraphQueryService.get_graph_analytics_summary()
        return render(request, self.template_name, {'analytics': analytics})


@method_decorator(admin_required, name='dispatch')
class TriggerGraphBuildView(View):
    def post(self, request):
        snapshot = GraphBuilderService.build_knowledge_graph()
        messages.success(request, f"Knowledge graph synchronized successfully! Created snapshot v{snapshot.version} ({snapshot.node_count} nodes, {snapshot.edge_count} edges).")
        return redirect('knowledge_graph:explorer')
