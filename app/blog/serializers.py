"""
Serializers for blog APIs
"""

from rest_framework import serializers
from core.models import Post, Comment, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class CommentSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.first_name')
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'body', 'owner', 'post', 'parent_comment', 'replies']

    def get_replies(self, obj):
        # Recursively serialize replies
        serializer = CommentSerializer(obj.replies, many=True)
        return serializer.data


class PostSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.first_name')
    comments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = ['id', 'title', 'body', 'owner', 'tags', 'comments', "image"]

    def _get_or_create_tags(self, tags, post):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            post.tags.add(tag_obj)

    def create(self, validated_data):
        """Create a post."""
        tags = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        self._get_or_create_tags(tags, post)

        return post

    def update(self, instance, validated_data):
        """Update a post."""
        tags = validated_data.pop('tags', None)
        if tags is not None:
            if len(tags) == 0:
                instance.tags.clear()
                self._get_or_create_tags(tags, instance)
            else:
                self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class PostImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to Posts."""

    class Meta:
        model = Post
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}
