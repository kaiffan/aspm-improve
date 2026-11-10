from django.contrib import admin

from dojo.scm.models import Commit, Repository


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ("url", "product", "provider", "default_branch")
    list_select_related = ("product",)
    search_fields = ("url", "external_id")
    raw_id_fields = ("product",)

    def get_readonly_fields(self, request, obj=None):
        return ("product", "url") if obj else ()


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    list_display = ("sha", "repository", "branch", "committed_at")
    list_select_related = ("repository",)
    search_fields = ("^sha", "repository__url")
    raw_id_fields = ("repository",)

    def get_readonly_fields(self, request, obj=None):
        return ("repository", "sha") if obj else ()
