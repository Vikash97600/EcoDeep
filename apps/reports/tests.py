from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apps.libraries.models import Category, Library, ProgrammingLanguage
from apps.reports.models import (
    PublicationFormatChoices,
)
from apps.reports.services.artifact_bundle_service import ArtifactBundleService
from apps.reports.services.export_service import ExportService
from apps.reports.services.ieee_paper_generator_service import IEEEPaperGeneratorService
from apps.reports.services.latex_table_service import LaTeXTableService
from apps.reports.services.narrative_service import NarrativeService
from apps.reports.services.thesis_generator_service import ThesisGeneratorService
from apps.users.models import Role, RoleChoices, UserProfile


class ResearchReportTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.researcher_role = Role.objects.create(role_name=RoleChoices.RESEARCHER)
        self.user = User.objects.create_user(username='report_user', password='Password123!')
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.role = self.researcher_role
        profile.save()

        self.lang = ProgrammingLanguage.objects.create(language_name='Python', slug='python')
        self.cat = Category.objects.create(category_name='JSON Parsers', slug='json-parsers')

        self.lib_a = Library.objects.create(
            library_name='json_std',
            official_name='json',
            current_version='3.11.0',
            programming_language=self.lang,
            category=self.cat
        )

    def test_latex_table_service(self):
        candidates = [
            {'library_name': 'ujson', 'execution_time_ms': 38.5, 'cpu_utilization_pct': 18.2, 'ram_rss_mb': 24.0, 'energy_joules': 2.15, 'green_score': 91.5}
        ]
        latex_str = LaTeXTableService.generate_benchmark_latex_table(candidates)
        self.assertIn(r"\begin{table}", latex_str)
        self.assertIn(r"\toprule", latex_str)
        self.assertIn("ujson", latex_str)

    def test_narrative_service(self):
        narrative = NarrativeService.generate_findings_narrative("JSON Parsers", "ujson", "json", 62.5)
        self.assertIn("ujson", narrative)
        self.assertIn("ANOVA", narrative)

        threats = NarrativeService.generate_threats_to_validity_narrative()
        self.assertIn("Internal Validity", threats)

    def test_thesis_generator_service(self):
        report = ThesisGeneratorService.generate_dissertation(self.cat, author_name="Vikash Kumar")
        self.assertIsNotNone(report)
        self.assertEqual(report.publication_format, PublicationFormatChoices.MCA_DISSERTATION)
        self.assertIn("Chapter 1: Introduction", report.content_markdown)
        self.assertIn(r"\documentclass{report}", report.content_latex)

    def test_ieee_paper_generator_service(self):
        report = IEEEPaperGeneratorService.generate_ieee_paper(self.cat, author_name="Vikash Kumar")
        self.assertIsNotNone(report)
        self.assertEqual(report.publication_format, PublicationFormatChoices.IEEE_CONFERENCE)
        self.assertIn(r"\documentclass[conference]{IEEEtran}", report.content_latex)
        self.assertTrue(report.checklist.meets_ieee_standards)

    def test_artifact_bundle_service(self):
        report = IEEEPaperGeneratorService.generate_ieee_paper(self.cat)
        pkg = ArtifactBundleService.generate_replication_package(report)
        self.assertIsNotNone(pkg)
        self.assertEqual(len(pkg.sha256_checksum), 64)

    def test_export_service(self):
        report = IEEEPaperGeneratorService.generate_ieee_paper(self.cat)
        resp_tex = ExportService.export_document(report, 'LATEX')
        self.assertEqual(resp_tex.status_code, 200)
        self.assertEqual(resp_tex['Content-Type'], 'text/plain; charset=utf-8')

        resp_md = ExportService.export_document(report, 'MARKDOWN')
        self.assertEqual(resp_md.status_code, 200)

        resp_json = ExportService.export_document(report, 'JSON')
        self.assertEqual(resp_json.status_code, 200)

    def test_report_views(self):
        self.client.login(username='report_user', password='Password123!')

        res_center = self.client.get(reverse('reports:reports_center'))
        self.assertEqual(res_center.status_code, 200)

        res_thesis = self.client.get(reverse('reports:thesis_generator'))
        self.assertEqual(res_thesis.status_code, 200)

        res_ieee = self.client.get(reverse('reports:ieee_generator'))
        self.assertEqual(res_ieee.status_code, 200)

        res_art = self.client.get(reverse('reports:artifact_packages'))
        self.assertEqual(res_art.status_code, 200)

        res_csv = self.client.get(reverse('reports:export_csv', kwargs={'report_type': 'research', 'format_type': 'csv'}))
        self.assertEqual(res_csv.status_code, 200)
