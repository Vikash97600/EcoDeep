from typing import List, Dict, Any
from apps.libraries.models import Library
from apps.knowledge_graph.models import (
    KnowledgeGraphNode, KnowledgeGraphEdge, NodeTypeChoices, RelationshipTypeChoices
)

class GraphQueryService:
    """Executes multi-hop graph queries, traversal algorithms, and alternative library lookups."""

    @staticmethod
    def find_alternative_libraries(library: Library, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Traverses knowledge graph to discover similar and alternative libraries."""
        node = KnowledgeGraphNode.objects.filter(node_type=NodeTypeChoices.LIBRARY, entity_id=library.id).first()
        if not node:
            return []

        results = []
        visited_ids = {node.id}

        # 1-hop outgoing and incoming similarity edges
        edges = KnowledgeGraphEdge.objects.filter(
            source_node=node,
            relationship_type__in=[RelationshipTypeChoices.DIRECT_REPLACEMENT, RelationshipTypeChoices.FUNCTIONAL_ALTERNATIVE, RelationshipTypeChoices.COMPETES_WITH]
        ).select_related('target_node')

        for edge in edges:
            target = edge.target_node
            if target.id not in visited_ids and target.node_type == NodeTypeChoices.LIBRARY:
                visited_ids.add(target.id)
                results.append({
                    'library_id': target.entity_id,
                    'library_name': target.label,
                    'relationship_type': edge.relationship_type,
                    'similarity_score': edge.weight,
                    'confidence_score': edge.confidence_score,
                    'hop_distance': 1,
                    'pagerank': target.pagerank_score
                })

        # 2-hop Category siblings if 1-hop sparse
        if len(results) < 3:
            cat_edges = KnowledgeGraphEdge.objects.filter(source_node=node, relationship_type=RelationshipTypeChoices.BELONGS_TO)
            for ce in cat_edges:
                cat_node = ce.target_node
                sibling_edges = KnowledgeGraphEdge.objects.filter(target_node=cat_node, relationship_type=RelationshipTypeChoices.BELONGS_TO).exclude(source_node=node)
                for se in sibling_edges:
                    sib = se.source_node
                    if sib.id not in visited_ids and sib.node_type == NodeTypeChoices.LIBRARY:
                        visited_ids.add(sib.id)
                        results.append({
                            'library_id': sib.entity_id,
                            'library_name': sib.label,
                            'relationship_type': 'CATEGORY_SIBLING',
                            'similarity_score': 0.50,
                            'confidence_score': 70.0,
                            'hop_distance': 2,
                            'pagerank': sib.pagerank_score
                        })

        # Sort by similarity score descending, then PageRank
        results.sort(key=lambda x: (x['similarity_score'], x['pagerank']), reverse=True)
        return results

    @staticmethod
    def get_graph_analytics_summary() -> Dict[str, Any]:
        """Calculates global knowledge graph statistics and identifies hub entities."""
        total_nodes = KnowledgeGraphNode.objects.count()
        total_edges = KnowledgeGraphEdge.objects.count()
        
        top_hubs = KnowledgeGraphNode.objects.order_by('-pagerank_score')[:5]
        top_connected = KnowledgeGraphNode.objects.order_by('-in_degree')[:5]

        return {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'density': round(total_edges / max(1, total_nodes * (total_nodes - 1)), 4) if total_nodes > 1 else 0.0,
            'top_hubs': list(top_hubs.values('label', 'node_type', 'pagerank_score', 'in_degree')),
            'top_connected': list(top_connected.values('label', 'in_degree', 'out_degree'))
        }
