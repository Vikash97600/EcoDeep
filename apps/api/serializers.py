from django.contrib.auth.models import User
from rest_framework import serializers

from apps.benchmark.models import (
    BenchmarkDataset,
    BenchmarkResult,
    BenchmarkSession,
    BenchmarkTask,
)
from apps.libraries.models import Category, Library, LibraryVersion, ProgrammingLanguage
from apps.recommendation.models import (
    GreenScore,
    RecommendationItem,
    RecommendationRecord,
    WeightProfile,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']


class ProgrammingLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgrammingLanguage
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class LibrarySerializer(serializers.ModelSerializer):
    programming_language = ProgrammingLanguageSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Library
        fields = '__all__'


class LibraryVersionSerializer(serializers.ModelSerializer):
    library = LibrarySerializer(read_only=True)

    class Meta:
        model = LibraryVersion
        fields = '__all__'


class BenchmarkDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkDataset
        fields = '__all__'


class BenchmarkTaskSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    dataset = BenchmarkDatasetSerializer(read_only=True)

    class Meta:
        model = BenchmarkTask
        fields = '__all__'


class BenchmarkSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkSession
        fields = '__all__'


class BenchmarkResultSerializer(serializers.ModelSerializer):
    library_version = LibraryVersionSerializer(read_only=True)
    task = BenchmarkTaskSerializer(read_only=True)
    dataset = BenchmarkDatasetSerializer(read_only=True)

    class Meta:
        model = BenchmarkResult
        fields = '__all__'


class WeightProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightProfile
        fields = '__all__'


class GreenScoreSerializer(serializers.ModelSerializer):
    library_version = LibraryVersionSerializer(read_only=True)
    task = BenchmarkTaskSerializer(read_only=True)
    weight_profile = WeightProfileSerializer(read_only=True)

    class Meta:
        model = GreenScore
        fields = '__all__'


class RecommendationItemSerializer(serializers.ModelSerializer):
    recommended_version = LibraryVersionSerializer(read_only=True)

    class Meta:
        model = RecommendationItem
        fields = '__all__'


class RecommendationRecordSerializer(serializers.ModelSerializer):
    target_library = LibrarySerializer(read_only=True)
    task = BenchmarkTaskSerializer(read_only=True)
    items = RecommendationItemSerializer(many=True, read_only=True)

    class Meta:
        model = RecommendationRecord
        fields = '__all__'
