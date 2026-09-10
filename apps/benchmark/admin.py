from django.contrib import admin

from apps.benchmark.models import (
    BenchmarkDataset,
    BenchmarkJob,
    BenchmarkResult,
    BenchmarkSession,
    BenchmarkTask,
)


@admin.register(BenchmarkDataset)
class BenchmarkDatasetAdmin(admin.ModelAdmin):
    list_display = ('dataset_name', 'dataset_category', 'dataset_size_bytes', 'status')
    list_filter = ('dataset_category', 'status')
    search_fields = ('dataset_name', 'description')


@admin.register(BenchmarkTask)
class BenchmarkTaskAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'category', 'iterations', 'status')
    list_filter = ('category', 'status')
    search_fields = ('task_name', 'description')


class BenchmarkJobInline(admin.TabularInline):
    model = BenchmarkJob
    extra = 0


@admin.register(BenchmarkSession)
class BenchmarkSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_name', 'admin', 'machine_name', 'status', 'start_time')
    list_filter = ('status', 'operating_system')
    search_fields = ('session_name', 'machine_name', 'cpu')
    inlines = [BenchmarkJobInline]


@admin.register(BenchmarkJob)
class BenchmarkJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'library_version', 'task', 'status', 'priority')
    list_filter = ('status', 'priority')
    search_fields = ('library_version__library__library_name', 'task__task_name')


@admin.register(BenchmarkResult)
class BenchmarkResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'library_version', 'task', 'execution_time', 'energy', 'green_score')
    list_filter = ('session', 'library_version__library__category')
    search_fields = ('library_version__library__library_name', 'task__task_name')
