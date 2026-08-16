from django.http import HttpResponse
from apps.reports.models import AcademicReport, DocumentFormatChoices

class ExportService:
    """Exports academic manuscripts in LaTeX, Markdown, HTML, or JSON formats."""

    @staticmethod
    def export_document(report: AcademicReport, format_choice: str = DocumentFormatChoices.LATEX) -> HttpResponse:
        """Returns appropriate HTTP file response for downloading manuscripts."""
        clean_title = report.title.replace(' ', '_').replace(':', '')[:30]

        if format_choice == DocumentFormatChoices.LATEX:
            response = HttpResponse(report.content_latex, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{clean_title}.tex"'
            return response
        elif format_choice == DocumentFormatChoices.MARKDOWN:
            response = HttpResponse(report.content_markdown, content_type='text/markdown; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{clean_title}.md"'
            return response
        elif format_choice == DocumentFormatChoices.JSON:
            payload = {
                'title': report.title,
                'author': report.author_name,
                'abstract': report.abstract,
                'publication_format': report.publication_format,
                'bibliography': report.bibliography_bibtex,
                'markdown': report.content_markdown
            }
            import json
            response = HttpResponse(json.dumps(payload, indent=2), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{clean_title}.json"'
            return response
        else:
            # HTML fallback
            html_doc = f"<html><head><title>{report.title}</title></head><body><pre>{report.content_markdown}</pre></body></html>"
            response = HttpResponse(html_doc, content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="{clean_title}.html"'
            return response
