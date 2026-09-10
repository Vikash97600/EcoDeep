from django.db import models

from apps.core.models import TimeStampedModel
from apps.libraries.models import Library


class NodeTypeChoices(models.TextChoices):
    LIBRARY = 'LIBRARY', 'Software Library Node'
    CATEGORY = 'CATEGORY', 'Functional Task Category Node'
    LANGUAGE = 'LANGUAGE', 'Programming Language Node'
    BENCHMARK_TASK = 'BENCHMARK_TASK', 'Benchmark Workload Task Node'


class RelationshipTypeChoices(models.TextChoices):
    DIRECT_REPLACEMENT = 'DIRECT_REPLACEMENT', 'Direct Drop-in Replacement (API Compatible)'
    FUNCTIONAL_ALTERNATIVE = 'FUNCTIONAL_ALTERNATIVE', 'Functional Alternative'
    COMPETES_WITH = 'COMPETES_WITH', 'Competes With (Same Domain)'
    BELONGS_TO = 'BELONGS_TO', 'Belongs to Category'
    IMPLEMENTS_LANGUAGE = 'IMPLEMENTS_LANGUAGE', 'Written in Language'
    DEPENDS_ON = 'DEPENDS_ON', 'Direct Software Dependency'
    EXTENDS = 'EXTENDS', 'Extends / Wraps Library'


class KnowledgeGraphNode(TimeStampedModel):
    """Represents an entity node in the software dependency knowledge graph."""
    node_type = models.CharField(max_length=30, choices=NodeTypeChoices.choices)
    entity_id = models.PositiveIntegerField(help_text="Primary key of source entity (e.g. Library.id)")
    label = models.CharField(max_length=150, db_index=True)
    properties_json = models.JSONField(default=dict, help_text="Node metadata and attributes")
    
    # Graph analytics metrics
    in_degree = models.PositiveIntegerField(default=0)
    out_degree = models.PositiveIntegerField(default=0)
    pagerank_score = models.FloatField(default=1.0, help_text="Calculated PageRank centrality score")

    class Meta:
        verbose_name = "Knowledge Graph Node"
        verbose_name_plural = "Knowledge Graph Nodes"
        unique_together = ('node_type', 'entity_id')
        ordering = ['label']

    def __str__(self):
        return f"{self.label} [{self.get_node_type_display()}] (PR: {self.pagerank_score:.3f})"


class KnowledgeGraphEdge(TimeStampedModel):
    """Represents a directed typed relationship between two entities in the knowledge graph."""
    source_node = models.ForeignKey(KnowledgeGraphNode, on_delete=models.CASCADE, related_name='outgoing_edges')
    target_node = models.ForeignKey(KnowledgeGraphNode, on_delete=models.CASCADE, related_name='incoming_edges')
    relationship_type = models.CharField(max_length=40, choices=RelationshipTypeChoices.choices)
    
    weight = models.FloatField(default=1.0, help_text="Edge weight (e.g. similarity score or energy differential)")
    confidence_score = models.FloatField(default=100.0, help_text="Relationship confidence (0-100%)")
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Knowledge Graph Edge"
        verbose_name_plural = "Knowledge Graph Edges"
        ordering = ['-weight']

    def __str__(self):
        return f"{self.source_node.label} --[{self.relationship_type}]--> {self.target_node.label} (w={self.weight:.2f})"


class LibraryEmbedding(TimeStampedModel):
    """Stores text embedding vectors derived from library descriptions and README documentation."""
    library = models.OneToOneField(Library, on_delete=models.CASCADE, related_name='embedding')
    embedding_type = models.CharField(max_length=30, default='TF_IDF')
    vector_json = models.JSONField(default=dict, help_text="Sparse or dense term weight vector")
    dimension = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Library Embedding"
        verbose_name_plural = "Library Embeddings"

    def __str__(self):
        return f"Embedding for {self.library.library_name} (dim={self.dimension})"


class SimilarityScore(TimeStampedModel):
    """Precomputed pairwise similarity scores between libraries."""
    source_library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='source_similarities')
    target_library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='target_similarities')
    
    cosine_similarity = models.FloatField(default=0.0)
    jaccard_similarity = models.FloatField(default=0.0)
    composite_similarity = models.FloatField(default=0.0, help_text="Hybrid composite similarity score (0.0 - 1.0)")
    
    is_discovered = models.BooleanField(default=True, help_text="Automatically discovered by NLP pipeline")
    relationship_type = models.CharField(max_length=40, choices=RelationshipTypeChoices.choices, default=RelationshipTypeChoices.FUNCTIONAL_ALTERNATIVE)

    class Meta:
        verbose_name = "Similarity Score"
        verbose_name_plural = "Similarity Scores"
        unique_together = ('source_library', 'target_library')
        ordering = ['-composite_similarity']

    def __str__(self):
        return f"{self.source_library.library_name} <-> {self.target_library.library_name} ({self.composite_similarity:.2f})"


class GraphSnapshot(TimeStampedModel):
    """Immutable periodic snapshot of the entire knowledge graph."""
    version = models.CharField(max_length=20, default='1.0.0')
    node_count = models.PositiveIntegerField(default=0)
    edge_count = models.PositiveIntegerField(default=0)
    graph_density = models.FloatField(default=0.0)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    summary_metrics = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Graph Snapshot"
        verbose_name_plural = "Graph Snapshots"
        ordering = ['-created_at']

    def __str__(self):
        return f"Graph Snapshot v{self.version} ({self.node_count} nodes, {self.edge_count} edges)"
