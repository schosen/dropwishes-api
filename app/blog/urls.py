"""
URL mappings for the blog API.
"""

from django.urls import path
from blog import views

app_name = 'blog'

urlpatterns = [
    path('posts/', views.PostListCreateView.as_view(), name='post-list'),
    path(
        'posts/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'
    ),
    path(
        'comments/',
        views.CommentListCreateView.as_view(),
        name='comment-list',
    ),
    path(
        'comments/<int:pk>/',
        views.CommentDetailView.as_view(),
        name='comment-detail',
    ),
    path('tags/', views.TagListView.as_view(), name='tag-list'),
    path(
        'tags/<int:pk>/',
        views.TagDetailView.as_view(),
        name='tag-detail',
    ),
]
