from django.contrib.auth.models import User
from django.db import models

from apps.core.models import TimeStampedModel
from apps.libraries.models import Category


class PublicationFormatChoices(models.TextChoices):
    MCA_DISSERTATION = 'MCA_DISSERTATION', 'MCA Research Master Dissertation (Chapters 1-8)'
    IEEE_CONFERENCE = 'IEEE_CONFERENCE', 'IEEE Conference Paper (Two-Column IEEEtran)'
    ACM_CONFERENCE = 'ACM_CONFERENCE', 'ACM Conference Proceedings (ACM sigconf)'
    TECHNICAL_REPORT = 'TECHNICAL_REPORT', 'Technical Benchmark & Evaluation Report'
    BENCHMARK_REPORT = 'BENCHMARK_REPORT', 'Empirical Telemetry Performance Audit'
    OPEN_SCIENCE_BUNDLE = 'OPEN_SCIENCE_BUNDLE', 'Open Science Replication Package'


class DocumentFormatChoices(models.TextChoices):
    MARKDOWN = 'MARKDOWN', 'Markdown (.md)'
    LATEX = 'LATEX', 'LaTeX Source (.tex)'
    HTML = 'HTML', 'HTML Report (.html)'
    JSON = 'JSON', 'Structured JSON (.json)'
    PDF = 'PDF', 'Portable Document Format (.pdf)'


class GeneratedReport(TimeStampedModel):
    """Tracks dynamically generated PDF and CSV report artifacts (legacy compatible)."""
    report_name = models.CharField(max_length=200)
    type = models.CharField(max_length=30, default='CATEGORY')
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    generated_on = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='reports/pdf/', blank=True, null=True)
    csv_file = models.FileField(upload_to='reports/csv/', blank=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Generated Report"
        verbose_name_plural = "Generated Reports"
        ordering = ['-generated_on']


class AcademicReport(TimeStampedModel):
    """Stores full academic manuscripts, theses, and IEEE/ACM conference papers."""
    title = models.CharField(max_length=255)
    publication_format = models.CharField(max_length=30, choices=PublicationFormatChoices.choices, default=PublicationFormatChoices.IEEE_CONFERENCE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='academic_reports')
    author_name = models.CharField(max_length=150, default="Vikash Kumar & Research Team")
    affiliation = models.CharField(max_length=200, default="Department of Computer Science & Engineering")
    
    abstract = models.TextField()
    keywords = models.CharField(max_length=255, default="Green Software Engineering, Energy Benchmarking, Carbon Intensity, MCDM, TOPSIS, EcoDep")
    
    content_markdown = models.TextField(help_text="Renderable Markdown manuscript")
    content_latex = models.TextField(help_text="Publication-ready LaTeX source code")
    bibliography_bibtex = models.TextField(help_text="BibTeX reference entries")
    
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Academic Report & Publication"
        verbose_name_plural = "Academic Reports & Publications"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.get_publication_format_display()}]"


class ReportSection(TimeStampedModel):
    """Structured individual section within an academic report."""
    report = models.ForeignKey(AcademicReport, on_delete=models.CASCADE, related_name='sections')
    section_number = models.CharField(max_length=20, default="1.0")
    section_title = models.CharField(max_length=200)
    section_type = models.CharField(max_length=50, default='BODY')
    body_text = models.TextField()
    table_latex = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Report Section"
        verbose_name_plural = "Report Sections"
        ordering = ['order']


class ResearchArtifactPackage(TimeStampedModel):
    """Open Science replication bundle containing dataset manifests and replication scripts."""
    report = models.ForeignKey(AcademicReport, on_delete=models.CASCADE, related_name='artifact_packages')
    title = models.CharField(max_length=200)
    package_type = models.CharField(max_length=50, default="FULL_REPLICATION_PACKAGE")
    archive_manifest_json = models.JSONField(default=dict)
    sha256_checksum = models.CharField(max_length=64)
    replication_instructions = models.TextField()

    class Meta:
        verbose_name = "Research Artifact Package"
        verbose_name_plural = "Research Artifact Packages"
        ordering = ['-created_at']


class PublicationChecklist(TimeStampedModel):
    """IEEE / ICSE submission readiness checklist."""
    report = models.OneToOneField(AcademicReport, on_delete=models.CASCADE, related_name='checklist')
    meets_ieee_standards = models.BooleanField(default=True)
    double_blind_ready = models.BooleanField(default=True)
    artifacts_verified = models.BooleanField(default=True)
    reproducibility_score = models.FloatField(default=98.5)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Publication Checklist"
        verbose_name_plural = "Publication Checklists"
