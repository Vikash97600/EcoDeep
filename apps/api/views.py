from django.db.models import Avg
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAdminUserOrReadOnly, IsResearcherOrAdmin
from apps.api.serializers import (
    BenchmarkResultSerializer,
    BenchmarkSessionSerializer,
    BenchmarkTaskSerializer,
    GreenScoreSerializer,
    LibrarySerializer,
    LibraryVersionSerializer,
    RecommendationRecordSerializer,
)
from apps.benchmark.models import (
    BenchmarkResult,
    BenchmarkSession,
    BenchmarkTask,
)
from apps.libraries.models import Library, LibraryVersion
from apps.recommendation.models import GreenScore, RecommendationRecord
from apps.recommendation.services.recommendation_service import RecommendationService


class LibraryViewSet(viewsets.ModelViewSet):
    queryset = Library.objects.select_related('category', 'programming_language').all()
    serializer_class = LibrarySerializer
    permission_classes = [IsAdminUserOrReadOnly]
    filterset_fields = ['category', 'programming_language', 'status']
    search_fields = ['library_name', 'official_name']


class LibraryVersionViewSet(viewsets.ModelViewSet):
    queryset = LibraryVersion.objects.select_related('library').all()
    serializer_class = LibraryVersionSerializer
    permission_classes = [IsAdminUserOrReadOnly]


class BenchmarkTaskViewSet(viewsets.ModelViewSet):
    queryset = BenchmarkTask.objects.select_related('category', 'dataset').all()
    serializer_class = BenchmarkTaskSerializer
    permission_classes = [IsResearcherOrAdmin]


class BenchmarkSessionViewSet(viewsets.ModelViewSet):
    queryset = BenchmarkSession.objects.all()
    serializer_class = BenchmarkSessionSerializer
    permission_classes = [IsResearcherOrAdmin]


class BenchmarkResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BenchmarkResult.objects.select_related(
        'session', 'library_version__library', 'task', 'dataset'
    ).order_by('-created_at')
    serializer_class = BenchmarkResultSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['task', 'dataset', 'library_version']


class GreenScoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GreenScore.objects.select_related(
        'library_version__library', 'task', 'weight_profile'
    ).order_by('-score')
    serializer_class = GreenScoreSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RecommendationRecord.objects.select_related('target_library', 'task').prefetch_related('items').all()
    serializer_class = RecommendationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def query(self, request):
        target_id = request.data.get('target_library_id')
        task_id = request.data.get('task_id')
        profile_type = request.data.get('profile_type', 'BEST_OVERALL')

        if not target_id or not task_id:
            return Response({'error': 'target_library_id and task_id are required fields.'}, status=status.HTTP_400_BAD_REQUEST)

        rec_record = RecommendationService.generate_recommendation(
            target_library_id=int(target_id),
            task_id=int(task_id),
            profile_type=profile_type,
            user=request.user
        )
        serializer = self.get_serializer(rec_record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'status': 'HEALTHY',
            'platform': 'EcoDep API Gateway v1',
            'database': 'CONNECTED',
            'version': '1.0.0'
        }, status=status.HTTP_200_OK)


class MetricsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'total_libraries': Library.objects.count(),
            'total_benchmark_sessions': BenchmarkSession.objects.count(),
            'total_results_stored': BenchmarkResult.objects.count(),
            'total_green_scores': GreenScore.objects.count(),
            'total_recommendations_served': RecommendationRecord.objects.count(),
            'average_green_score': float(GreenScore.objects.aggregate(Avg('score'))['score__avg'] or 0.0)
        }, status=status.HTTP_200_OK)
