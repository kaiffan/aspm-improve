from dojo.scm.api.views import CommitViewSet, RepositoryViewSet


def add_scm_urls(router):
    router.register("repositories", RepositoryViewSet, basename="repository")
    router.register("commits", CommitViewSet, basename="commit")
