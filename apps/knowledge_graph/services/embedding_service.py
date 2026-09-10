import math
from collections import Counter

from apps.knowledge_graph.models import LibraryEmbedding
from apps.knowledge_graph.services.nlp_service import NLPService
from apps.libraries.models import Library


class EmbeddingService:
    """Computes TF-IDF vector embeddings for software libraries and maintains the vector store."""

    @staticmethod
    def generate_library_embedding(library: Library) -> LibraryEmbedding:
        """Constructs a normalized TF-IDF term vector for a library."""
        # Combine library textual metadata
        combined_text = f"{library.library_name} {library.official_name} {library.description} {library.category.category_name if library.category else ''}"
        tokens = NLPService.tokenize(combined_text)

        if not tokens:
            tokens = [library.library_name.lower()]

        term_counts = Counter(tokens)
        total_tokens = len(tokens)

        # Term frequency (TF)
        tf_dict = {term: count / total_tokens for term, count in term_counts.items()}

        # Synthetic IDF scaling (higher weight for discriminative domain terms)
        tfidf_vector = {}
        for term, tf in tf_dict.items():
            idf = 1.5 if term in ['json', 'http', 'async', 'fast', 'parse', 'encode', 'decode', 'orm', 'db', 'cache'] else 1.0
            tfidf_vector[term] = round(tf * idf, 4)

        # Normalize vector to unit length
        mag_sq = sum(w * w for w in tfidf_vector.values())
        magnitude = math.sqrt(mag_sq) if mag_sq > 0 else 1.0

        normalized_vector = {t: round(w / magnitude, 4) for t, w in tfidf_vector.items()}

        embedding, _created = LibraryEmbedding.objects.update_or_create(
            library=library,
            defaults={
                'embedding_type': 'TF_IDF',
                'vector_json': normalized_vector,
                'dimension': len(normalized_vector)
            }
        )
        return embedding
