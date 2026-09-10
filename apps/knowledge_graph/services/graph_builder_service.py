import hashlib

from apps.knowledge_graph.models import (
    GraphSnapshot,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    NodeTypeChoices,
    RelationshipTypeChoices,
    SimilarityScore,
)
from apps.knowledge_graph.services.relationship_service import RelationshipService
from apps.libraries.models import Category, Library, ProgrammingLanguage


class GraphBuilderService:
    """Constructs the property knowledge graph from database entities and computed similarity relationships."""

    @staticmethod
    def build_knowledge_graph() -> GraphSnapshot:
        """Constructs/updates all graph nodes, edges, analytics metrics, and creates a snapshot."""
        # 1. Discover all similarity relationships first
        RelationshipService.discover_all_relationships(min_similarity_threshold=0.30)

        # 2. Synchronize Nodes
        # Library Nodes
        lib_nodes = {}
        for lib in Library.objects.select_related('category', 'programming_language').all():
            node, _ = KnowledgeGraphNode.objects.update_or_create(
                node_type=NodeTypeChoices.LIBRARY,
                entity_id=lib.id,
                defaults={
                    'label': lib.library_name,
                    'properties_json': {
                        'official_name': lib.official_name,
                        'category': lib.category.category_name if lib.category else 'Uncategorized',
                        'language': lib.programming_language.language_name if lib.programming_language else 'Unknown',
                        'version': lib.current_version
                    }
                }
            )
            lib_nodes[lib.id] = node

        # Category Nodes
        cat_nodes = {}
        for cat in Category.objects.all():
            node, _ = KnowledgeGraphNode.objects.update_or_create(
                node_type=NodeTypeChoices.CATEGORY,
                entity_id=cat.id,
                defaults={
                    'label': cat.category_name,
                    'properties_json': {'slug': cat.slug, 'description': cat.description}
                }
            )
            cat_nodes[cat.id] = node

        # Language Nodes
        lang_nodes = {}
        for lang in ProgrammingLanguage.objects.all():
            node, _ = KnowledgeGraphNode.objects.update_or_create(
                node_type=NodeTypeChoices.LANGUAGE,
                entity_id=lang.id,
                defaults={
                    'label': lang.language_name,
                    'properties_json': {'slug': lang.slug}
                }
            )
            lang_nodes[lang.id] = node

        # 3. Synchronize Structural Edges
        # Library -> Category (BELONGS_TO)
        for lib in Library.objects.filter(category__isnull=False):
            if lib.id in lib_nodes and lib.category_id in cat_nodes:
                KnowledgeGraphEdge.objects.get_or_create(
                    source_node=lib_nodes[lib.id],
                    target_node=cat_nodes[lib.category_id],
                    relationship_type=RelationshipTypeChoices.BELONGS_TO,
                    defaults={'weight': 1.0, 'confidence_score': 100.0}
                )

        # Library -> Language (IMPLEMENTS_LANGUAGE)
        for lib in Library.objects.filter(programming_language__isnull=False):
            if lib.id in lib_nodes and lib.programming_language_id in lang_nodes:
                KnowledgeGraphEdge.objects.get_or_create(
                    source_node=lib_nodes[lib.id],
                    target_node=lang_nodes[lib.programming_language_id],
                    relationship_type=RelationshipTypeChoices.IMPLEMENTS_LANGUAGE,
                    defaults={'weight': 1.0, 'confidence_score': 100.0}
                )

        # Library <-> Library (Similarity Edges)
        for sim in SimilarityScore.objects.all():
            if sim.source_library_id in lib_nodes and sim.target_library_id in lib_nodes:
                KnowledgeGraphEdge.objects.update_or_create(
                    source_node=lib_nodes[sim.source_library_id],
                    target_node=lib_nodes[sim.target_library_id],
                    relationship_type=sim.relationship_type,
                    defaults={
                        'weight': sim.composite_similarity,
                        'confidence_score': round(sim.composite_similarity * 100, 1),
                        'metadata_json': {'cosine': sim.cosine_similarity, 'jaccard': sim.jaccard_similarity}
                    }
                )

        # 4. Compute Degree and PageRank Centrality
        nodes = list(KnowledgeGraphNode.objects.all())
        total_nodes = len(nodes)
        
        for n in nodes:
            n.in_degree = n.incoming_edges.count()
            n.out_degree = n.outgoing_edges.count()
            # Simple PageRank approximation based on degree centrality
            deg = n.in_degree + n.out_degree
            n.pagerank_score = round(1.0 + (deg / max(1, total_nodes)) * 2.0, 3)
            n.save(update_fields=['in_degree', 'out_degree', 'pagerank_score'])

        total_edges = KnowledgeGraphEdge.objects.count()
        density = round(total_edges / max(1, total_nodes * (total_nodes - 1)), 4) if total_nodes > 1 else 0.0

        # 5. Persist Graph Snapshot
        version_str = f"1.0.{GraphSnapshot.objects.count() + 1}"
        hash_content = f"{total_nodes}-{total_edges}-{density}-{version_str}"
        checksum = hashlib.sha256(hash_content.encode('utf-8')).hexdigest()

        snapshot = GraphSnapshot.objects.create(
            version=version_str,
            node_count=total_nodes,
            edge_count=total_edges,
            graph_density=density,
            checksum_sha256=checksum,
            summary_metrics={'density': density, 'total_nodes': total_nodes, 'total_edges': total_edges}
        )

        return snapshot
