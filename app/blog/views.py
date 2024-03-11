"""
Views for the blog API.
"""

from core.models import Post, Comment, Tag
from rest_framework import generics, status
from blog.serializers import (
    PostSerializer,
    CommentSerializer,
    TagSerializer,
    PostImageSerializer,
)
from rest_framework.permissions import (
    DjangoModelPermissionsOrAnonReadOnly,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.authentication import TokenAuthentication
from user.permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response


class PostListCreateView(generics.ListCreateAPIView):
    """View for managing post list and create APIs."""

    serializer_class = PostSerializer
    queryset = Post.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [
        IsAdminOrReadOnly,
    ]

    def perform_create(self, serializer):
        print("self.request.user.is_staff", self.request.user.is_staff)
        serializer.save(owner=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for managing a single post APIs."""

    serializer_class = PostSerializer

    queryset = Post.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [
        IsAdminOrReadOnly,
    ]


class CommentListCreateView(generics.ListCreateAPIView):
    """View for managing comment List and Create APIs."""

    serializer_class = CommentSerializer
    queryset = Comment.objects.filter(parent_comment=None)
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        """create a new comment"""
        ## The below limits the amount of replies to parent comment
        ## And stops replies to replies. To make replies limitless remove this block of code.
        parent_comment_id = self.request.data.get('parent_comment')
        if parent_comment_id:
            # Check if the parent comment already has a reply
            if Comment.objects.filter(
                parent_comment=parent_comment_id
            ).exists():
                return Response(
                    {"error": "A parent comment can only have one reply."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if the parent comment is a reply
            parent_comment = Comment.objects.get(pk=parent_comment_id)
            if parent_comment.parent_comment is not None:
                return Response(
                    {"error": "Replies to replies are not allowed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        serializer.save(owner=self.request.user)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for managing a single comment APIs."""

    serializer_class = CommentSerializer
    queryset = Comment.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [
        IsOwnerOrReadOnly,
    ]


class TagListView(generics.ListAPIView):
    """View for managing tag List APIs."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        """create a new tag"""
        serializer.save(owner=self.request.user)


class TagDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for managing a single tag APIs."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrReadOnly]
