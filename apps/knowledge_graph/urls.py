from django.urls import path

from apps.knowledge_graph import views

app_name = 'knowledge_graph'

urlpatterns = [
    path('explorer/', views.KnowledgeGraphExplorerView.as_view(), name='explorer'),
    path('similarity/', views.SimilarLibrariesDiscoveryView.as_view(), name='similarity_discovery'),
    path('relationships/', views.RelationshipListView.as_view(), name='relationship_list'),
    path('analytics/', views.GraphAnalyticsView.as_view(), name='graph_analytics'),
    path('build/', views.TriggerGraphBuildView.as_view(), name='build_graph'),
]
