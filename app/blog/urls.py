"""
URL mappings for the blog API.
"""

from django.urls import path
from blog import views
from rest_framework.urlpatterns import format_suffix_patterns


urlpatterns = [
    path(
        'posts/', views.PostListCreateView.as_view(), name='post-list-create'
    ),
    path('posts/<int:pk>/', views.PostDetailView.as_view()),
    path(
        'comments/',
        views.CommentListCreateView.as_view(),
        name='comment-list-create',
    ),
    path(
        'comments/<int:pk>/',
        views.CommentDetailView.as_view(),
        name='comment-retrieve-update-destroy',
    ),
    path('tags/', views.TagListView.as_view(), name='tag-list'),
    path(
        'tags/<int:pk>/',
        views.TagDetailView.as_view(),
        name='comment-retrieve-update-destroy',
    ),
]

# urlpatterns = format_suffix_patterns(urlpatterns)
