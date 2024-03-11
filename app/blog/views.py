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
    queryset = Comment.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Only return top-level comments (parent_comment is None)
        return Comment.objects.filter(parent_comment=None)

    def create(self, request, *args, **kwargs):
        """overide create method to provide custom validation"""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check if creating a parent comment or a reply
        parent_comment_id = request.data.get('parent_comment')
        if parent_comment_id:
            # Check if the parent comment is a reply. stop replies to replies.
            parent_comment = Comment.objects.get(pk=parent_comment_id)
            if parent_comment.parent_comment is not None:
                return Response(
                    {"error": "Replies to replies are not allowed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if the parent comment already has a reply
            if Comment.objects.filter(
                parent_comment=parent_comment_id
            ).exists():
                return Response(
                    {"error": "A parent comment can only have one reply."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # For replies, only allow admin users
            if not IsAdminOrReadOnly().has_permission(request, self):
                return Response(
                    {"error": "You do not have permission to create a reply."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            # For parent comments, allow authenticated users
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_create(self, serializer):
        """create a new comment"""
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
