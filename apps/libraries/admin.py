from django.contrib import admin

from apps.libraries.models import (
    Category,
    Library,
    LibraryVersion,
    ProgrammingLanguage,
    SimilarLibraryMapping,
)


@admin.register(ProgrammingLanguage)
class ProgrammingLanguageAdmin(admin.ModelAdmin):
    list_display = ('language_name', 'slug', 'status')
    search_fields = ('language_name', 'slug')
    prepopulated_fields = {'slug': ('language_name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'slug', 'status')
    search_fields = ('category_name', 'description')
    prepopulated_fields = {'slug': ('category_name',)}


class LibraryVersionInline(admin.TabularInline):
    model = LibraryVersion
    extra = 1


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('library_name', 'programming_language', 'category', 'current_version', 'license', 'popularity_score', 'status')
    list_filter = ('programming_language', 'category', 'status', 'license')
    search_fields = ('library_name', 'official_name', 'description')
    inlines = [LibraryVersionInline]


@admin.register(SimilarLibraryMapping)
class SimilarLibraryMappingAdmin(admin.ModelAdmin):
    list_display = ('source_library', 'target_library', 'similarity_type', 'similarity_score', 'verified_by', 'status')
    list_filter = ('similarity_type', 'status')
    search_fields = ('source_library__library_name', 'target_library__library_name', 'reason')
