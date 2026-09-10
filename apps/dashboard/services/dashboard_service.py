from django.db.models import Avg

from apps.benchmark.models import (
    BenchmarkDataset,
    BenchmarkJob,
    BenchmarkResult,
    BenchmarkSession,
)
from apps.core.models import AuditLog
from apps.libraries.models import Library
from apps.recommendation.models import GreenScore, RecommendationRecord
from apps.users.models import UserProfile


class DashboardService:
    """Aggregates high-level telemetry and metrics for role-based workspaces."""

    @staticmethod
    def get_admin_metrics():
        return {
            'total_sessions': BenchmarkSession.objects.count(),
            'total_jobs': BenchmarkJob.objects.count(),
            'pending_jobs': BenchmarkJob.objects.filter(status='PENDING').count(),
            'running_jobs': BenchmarkJob.objects.filter(status='RUNNING').count(),
            'completed_jobs': BenchmarkJob.objects.filter(status='COMPLETED').count(),
            'failed_jobs': BenchmarkJob.objects.filter(status='FAILED').count(),
            'total_libraries': Library.objects.count(),
            'total_datasets': BenchmarkDataset.objects.count(),
            'total_users': UserProfile.objects.count(),
            'recent_logs': AuditLog.objects.select_related('user').order_by('-timestamp')[:8],
        }

    @staticmethod
    def get_researcher_metrics():
        return {
            'total_experiments': BenchmarkSession.objects.filter(status='COMPLETED').count(),
            'total_results': BenchmarkResult.objects.count(),
            'average_green_score': float(GreenScore.objects.aggregate(Avg('score'))['score__avg'] or 0.0),
            'top_green_scores': GreenScore.objects.select_related('library_version__library', 'task').order_by('-score')[:5],
            'recent_sessions': BenchmarkSession.objects.order_by('-start_time')[:5],
        }

    @staticmethod
    def get_developer_metrics():
        return {
            'total_recommendations': RecommendationRecord.objects.count(),
            'top_ranked_libraries': GreenScore.objects.select_related('library_version__library', 'task').order_by('-score')[:6],
            'recent_queries': RecommendationRecord.objects.select_related('target_library', 'task').order_by('-created_at')[:5],
        }
