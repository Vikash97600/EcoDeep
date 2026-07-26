from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator, MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel, StatusChoices

class SimilarityTypeChoices(models.TextChoices):
    DIRECT_REPLACEMENT = 'DIRECT', 'Direct Drop-in Replacement'
    FUNCTIONAL_EQUIVALENT = 'FUNCTIONAL', 'Functional Equivalent (Minor API differences)'
    PARADIGM_ALTERNATIVE = 'PARADIGM', 'Paradigm Alternative (Async / C-Extension)'


class ProgrammingLanguage(models.Model):
    """Represents target programming languages (Python, JavaScript, Java, Go, Rust)."""
    language_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='languages/logos/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)

    class Meta:
        verbose_name = "Programming Language"
        verbose_name_plural = "Programming Languages"
        ordering = ['language_name']

    def __str__(self):
        return self.language_name


class Category(models.Model):
    """Functional categories (e.g. Data Serialization, HTTP Requests, Image Resizing)."""
    category_name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap or FontAwesome icon class")
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)

    class Meta:
        verbose_name = "Functional Category"
        verbose_name_plural = "Functional Categories"
        ordering = ['category_name']

    def __str__(self):
        return self.category_name


class Library(TimeStampedModel):
    """Stores open-source third-party library metadata."""
    library_name = models.CharField(max_length=100, db_index=True)
    official_name = models.CharField(max_length=150)
    programming_language = models.ForeignKey(ProgrammingLanguage, on_delete=models.PROTECT, related_name='libraries')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='libraries')
    description = models.TextField()
    package_manager = models.CharField(max_length=50, default='PyPI')
    repository_url = models.URLField(validators=[URLValidator()], blank=True)
    documentation_url = models.URLField(validators=[URLValidator()], blank=True)
    homepage_url = models.URLField(validators=[URLValidator()], blank=True)
    current_version = models.CharField(max_length=30, help_text="Latest stable version pin")
    license = models.CharField(max_length=50, default='MIT')
    maintainer = models.CharField(max_length=100, blank=True)
    popularity_score = models.IntegerField(default=0, help_text="GitHub Stars / PyPI Rating")
    downloads = models.BigIntegerField(default=0, help_text="Monthly download statistics")
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)

    class Meta:
        verbose_name = "Software Library"
        verbose_name_plural = "Software Libraries"
        ordering = ['library_name']
        unique_together = ('library_name', 'programming_language')
        indexes = [
            models.Index(fields=['library_name', 'category']),
        ]

    def __str__(self):
        return f"{self.library_name} ({self.programming_language.language_name})"


class LibraryVersion(TimeStampedModel):
    """Tracks specific release versions of a candidate library."""
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=30)
    release_date = models.DateField(null=True, blank=True)
    release_notes = models.TextField(blank=True)
    supported_python_version = models.CharField(max_length=50, default='>=3.8')
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)

    class Meta:
        verbose_name = "Library Version"
        verbose_name_plural = "Library Versions"
        ordering = ['-release_date', '-version_number']
        unique_together = ('library', 'version_number')

    def __str__(self):
        return f"{self.library.library_name} v{self.version_number}"


class SimilarLibraryMapping(TimeStampedModel):
    """Maps functionally equivalent candidate libraries within a category."""
    source_library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='source_mappings')
    target_library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='target_mappings')
    similarity_type = models.CharField(max_length=30, choices=SimilarityTypeChoices.choices, default=SimilarityTypeChoices.FUNCTIONAL_EQUIVALENT)
    similarity_score = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], help_text="API Compatibility Score (0.00 to 1.00)")
    reason = models.TextField(help_text="Explanation of functional equivalence or minor API differences")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)

    class Meta:
        verbose_name = "Similar Library Mapping"
        verbose_name_plural = "Similar Library Mappings"
        unique_together = ('source_library', 'target_library')

    def __str__(self):
        return f"{self.source_library.library_name} <-> {self.target_library.library_name} ({self.similarity_score})"
