import re
from typing import List, Set

class NLPService:
    """Text preprocessing, tokenization, stop-word filtering, and term normalization."""

    STOP_WORDS: Set[str] = {
        'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and',
        'any', 'are', 'aren', 'as', 'at', 'be', 'because', 'been', 'before', 'being',
        'below', 'between', 'both', 'but', 'by', 'can', 'cannot', 'could', 'did', 'do',
        'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further',
        'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him',
        'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself',
        'let', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off',
        'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out',
        'over', 'own', 'same', 'she', 'should', 'so', 'some', 'such', 'than', 'that',
        'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they',
        'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was',
        'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why',
        'with', 'would', 'you', 'your', 'yours', 'yourself', 'yourselves', 'package', 'library', 'python'
    }

    @staticmethod
    def clean_text(text: str) -> str:
        """Removes HTML tags, URLs, special symbols, and converts to lowercase."""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'http\S+|www\S+', ' ', text)
        text = re.sub(r'[^a-zA-Z0-9\s_-]', ' ', text)
        return text.lower().strip()

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokenizes cleaned text into normalized non-stopword tokens."""
        cleaned = NLPService.clean_text(text)
        tokens = re.split(r'[\s_\-]+', cleaned)
        return [t for t in tokens if len(t) > 2 and t not in NLPService.STOP_WORDS]
