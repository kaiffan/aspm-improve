from django.urls import path

from dojo.scm.ui import views

urlpatterns = [
    path("product/<int:product_id>/repositories", views.repository_list, name="scm_repository_list"),
    path("repositories/<int:repository_id>", views.repository_detail, name="scm_repository_detail"),
    path("commits/<int:commit_id>", views.commit_detail, name="scm_commit_detail"),
    path("commits/<int:commit_id>/compare", views.commit_compare, name="scm_commit_compare"),
]
