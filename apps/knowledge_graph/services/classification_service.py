from apps.knowledge_graph.services.nlp_service import NLPService
from apps.libraries.models import Category, Library


class ClassificationService:
    """Automatically assigns and predicts functional task categories for libraries."""

    CATEGORY_KEYWORDS = {
        'JSON Parsers': {'json', 'parse', 'serialize', 'deserialize', 'encoder', 'decoder', 'ujson', 'orjson', 'fastjson', 'gson', 'moshi'},
        'HTTP Clients': {'http', 'request', 'client', 'rest', 'url', 'get', 'post', 'fetch', 'urllib', 'aiohttp', 'httpx'},
        'Database ORM': {'database', 'orm', 'sql', 'query', 'model', 'table', 'relational', 'sqlite', 'postgres', 'mysql'},
        'Image Processing': {'image', 'resize', 'crop', 'filter', 'raster', 'png', 'jpeg', 'pillow', 'opencv'},
        'Data Analysis': {'dataframe', 'matrix', 'tensor', 'array', 'analysis', 'statistics', 'numpy', 'pandas'}
    }

    @staticmethod
    def discover_category_for_library(library: Library) -> Category:
        """Determines best matching functional category from library textual metadata."""
        text = f"{library.library_name} {library.official_name} {library.description}"
        tokens = set(NLPService.tokenize(text))

        best_cat_name = None
        max_overlap = 0

        for cat_name, keywords in ClassificationService.CATEGORY_KEYWORDS.items():
            overlap = len(tokens & keywords)
            if overlap > max_overlap:
                max_overlap = overlap
                best_cat_name = cat_name

        if best_cat_name:
            category, _ = Category.objects.get_or_create(
                category_name=best_cat_name,
                defaults={'slug': best_cat_name.lower().replace(' ', '-'), 'description': f"Auto-discovered category: {best_cat_name}"}
            )
            return category

        return library.category
