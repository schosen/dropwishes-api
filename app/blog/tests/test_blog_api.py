"""
Tests for the blog API.
"""

from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Post, Comment, Tag, User


from blog.serializers import (
    CommentSerializer,
    PostSerializer,
)

POST_URL = reverse("blog:post-list")
COMMENT_URL = reverse("blog:comment-list")
TAG_URL = reverse("blog:tag-list")


def post_detail_url(post_id):
    """Create and return a post detail URL."""
    return reverse("blog:post-detail", args=[post_id])


def comment_detail_url(comment_id):
    """Create and return a comment detail URL."""
    return reverse("blog:comment-detail", args=[comment_id])


def tag_detail_url(tag_id):
    """Create and return a tag detail URL."""
    return reverse("blog:tag-detail", args=[tag_id])


def create_blog_post(user, **params):
    """Create and return a sample blog object."""
    defaults = {
        "title": "How to choose the best gift",
        "body": "Lorum ipsum",
        # "tags": [{"name": "gifts"}],
        # "image": "string",
    }
    defaults.update(params)

    obj = Post.objects.create(owner=user, **defaults)
    return obj


def create_comment(user, post, **params):
    """Create and return a sample comment object."""
    defaults = {"body": "Lorum ipsum", "post": post}
    defaults.update(params)

    obj = Comment.objects.create(owner=user, **defaults)
    return obj


class PublicWishlistAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create(
            first_name='admin', email="admin@example.com", is_staff=True
        )
        self.regular_user = User.objects.create(
            first_name='john', email="johndoe@example.com"
        )
        self.blog_post = create_blog_post(self.admin_user)
        self.comment = Comment.objects.create(
            owner=self.regular_user,
            body='Test Comment',
            post=self.blog_post,
        )
        self.tag = Tag.objects.create(name='Test Tag', user=self.admin_user)

    def test_post_unauthenticated_safe_request(self):
        """Test auth is not required for GET requests to Post API."""
        posts_res = self.client.get(POST_URL)
        post_res = self.client.get(post_detail_url(self.blog_post.id))

        self.assertEqual(posts_res.status_code, status.HTTP_200_OK)
        self.assertEqual(post_res.status_code, status.HTTP_200_OK)

    def test_comment_unauthenticated_safe_request(self):
        """Test auth is not required for GET requests to Comment API."""
        comments_res = self.client.get(COMMENT_URL)
        comment_res = self.client.get(comment_detail_url(self.comment.id))

        self.assertEqual(comments_res.status_code, status.HTTP_200_OK)
        self.assertEqual(comment_res.status_code, status.HTTP_200_OK)

    def test_tag_unauthenticated_safe_request(self):
        """Test auth is not required for GET requests to tag API."""
        tags_res = self.client.get(TAG_URL)
        tag_res = self.client.get(tag_detail_url(self.tag.id))

        self.assertEqual(tags_res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag_res.status_code, status.HTTP_200_OK)

    def test_post_authentication_required(self):
        """Test auth is required for Create and edit requests to Post API."""
        unauth_post = self.client.post(
            POST_URL,
            {
                "title": "How to choose the best gift",
                "body": "Lorum ipsum",
                "tags": [{"name": "gifts"}],
            },
        )
        self.assertEqual(unauth_post.status_code, status.HTTP_401_UNAUTHORIZED)

        payload = {"title": "change title", "body": "Lorum ipsum"}
        url = post_detail_url(self.blog_post.id)
        unauth_patch = self.client.patch(url, payload)

        self.assertEqual(
            unauth_patch.status_code, status.HTTP_401_UNAUTHORIZED
        )

        unauth_delete = self.client.delete(url)
        self.assertEqual(
            unauth_delete.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_comment_authentication_required(self):
        """
        Test auth is required for Create and edit
        requests to Comment API.
        """
        unauth_post = self.client.post(
            COMMENT_URL,
            {"body": "This is a dummy comment", "post": 1},
        )
        self.assertEqual(unauth_post.status_code, status.HTTP_401_UNAUTHORIZED)

        url = comment_detail_url(self.comment.id)
        payload = {"body": "change message"}

        unauth_patch = self.client.patch(url, payload)

        self.assertEqual(
            unauth_patch.status_code, status.HTTP_401_UNAUTHORIZED
        )
        unauth_delete = self.client.delete(url)
        self.assertEqual(
            unauth_delete.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_tag_authentication_required(self):
        """Test auth is required for edit requests to tag API."""

        url = tag_detail_url(self.tag.id)
        payload = {"body": "change message"}
        unauth_patch = self.client.patch(url, payload)

        self.assertEqual(
            unauth_patch.status_code, status.HTTP_401_UNAUTHORIZED
        )
        unauth_delete = self.client.delete(url)
        self.assertEqual(
            unauth_delete.status_code, status.HTTP_401_UNAUTHORIZED
        )


class PrivateWishlistApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create(
            first_name='admin', email="admin@example.com", is_staff=True
        )
        self.regular_user = User.objects.create(
            first_name='john', email="johndoe@example.com"
        )
        self.blog_post = create_blog_post(self.admin_user)

    def test_only_admin_can_create_posts(self):
        """
        test only admin can create posts.
        standard authenticated users cannot
        """
        payload = {
            "title": "admin post",
            "body": "this is an admin post",
            "tags": [{"name": "gifts"}],
        }
        self.client.force_authenticate(self.regular_user)
        reg_user_res = self.client.post(POST_URL, payload)
        self.assertEqual(reg_user_res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin_user)
        admin_user_res = self.client.post(POST_URL, payload)
        self.assertEqual(admin_user_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(admin_user_res.data['body'], payload["body"])
        self.assertEqual(admin_user_res.data['title'], payload["title"])

    def standard_user_delete_post_returns_error(self):
        """test if standard user deletes post it reurns error"""
        self.client.force_authenticate(self.regular_user)
        reg_user_res = self.client.delete(post_detail_url(self.blog_post.id))
        self.assertEqual(reg_user_res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Post.objects.filter(id=self.blog_post.id).exists())

    def test_only_admin_can_reply_to_comment(self):
        """
        test only admin can reply to comment.
        standard authenticated users cannot
        """
        comment = create_comment(self.regular_user, self.blog_post)
        payload = {
            "body": "This is a reply to a comment, only admins can do this",
            "post": self.blog_post.id,
            "parent_comment": comment.id,
        }
        self.client.force_authenticate(self.regular_user)
        user_res = self.client.post(COMMENT_URL, payload)
        self.assertEqual(user_res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin_user)
        admin_res = self.client.post(COMMENT_URL, payload)
        self.assertEqual(admin_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(admin_res.data['body'], payload["body"])

    def test_only_admin_can_update_tag(self):
        """
        test only admin can update a tag.
        standard authenticated users cannot
        """
        tag = Tag.objects.create(user=self.admin_user, name="Birthday")

        payload = {"name": "30th Birthday"}
        self.client.force_authenticate(self.regular_user)
        user_res = self.client.patch(tag_detail_url(tag.id), payload)
        self.assertEqual(user_res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin_user)
        admin_res = self.client.patch(tag_detail_url(tag.id), payload)
        self.assertEqual(admin_res.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_res.data['name'], payload["name"])

    def test_only_admin_can_delete_tag(self):
        """
        test only admin can delete a tag.
        standard authenticated users cannot
        """
        tag = Tag.objects.create(user=self.admin_user, name="Birthday")
        self.client.force_authenticate(self.regular_user)

        user_res = self.client.delete(tag_detail_url(tag.id))
        self.assertEqual(user_res.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.admin_user)
        admin_res = self.client.delete(tag_detail_url(tag.id))
        self.assertEqual(admin_res.status_code, status.HTTP_204_NO_CONTENT)

    def test_cant_reply_to_replies(self):
        """test you can't reply to replies"""
        comment = create_comment(user=self.regular_user, post=self.blog_post)
        reply = create_comment(
            user=self.admin_user, post=self.blog_post, parent_comment=comment
        )
        payload = {
            "post": self.blog_post.id,
            "body": "this is a reply to reply",
            "parent_comment": reply.id,
        }
        self.client.force_authenticate(self.regular_user)
        res = self.client.post(COMMENT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    def test_authenticated_users_can_create_comment(self):
        """test authorized users can create a comment"""
        payload = {
            "body": "this is a comment",
            "post": self.blog_post.id,
        }
        self.client.force_authenticate(self.regular_user)
        res = self.client.post(COMMENT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['body'], payload["body"])
        self.assertEqual(res.data['post'], payload["post"])

    def test_update_user_returns_error(self):
        """Test changing the comment user results in an error."""
        another_regular_user = User.objects.create(
            first_name='jess', email="jesspearson@example.com"
        )
        comment = create_comment(user=self.regular_user, post=self.blog_post)

        payload = {"owner": another_regular_user.id}
        url = comment_detail_url(comment.id)
        self.client.force_authenticate(self.regular_user)
        self.client.patch(url, payload)

        comment.refresh_from_db()
        self.assertEqual(comment.owner, self.regular_user)

    def test_delete_other_users_comment_error(self):
        """Test trying to delete another users comment gives error."""
        another_regular_user = User.objects.create(
            first_name='jess', email="jesspearson@example.com"
        )
        comment = create_comment(
            user=another_regular_user, post=self.blog_post
        )

        url = comment_detail_url(comment.id)
        self.client.force_authenticate(self.regular_user)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())

    # def test_admin_can_delete_other_users_comment(self):
    #     """Test admin can successfully delete another users comment."""
    #     comment = create_comment(user=self.regular_user, post=self.blog_post)

    #     url = comment_detail_url(comment.id)
    #     self.client.force_authenticate(self.admin_user)
    #     res = self.client.delete(url)

    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    def test_admin_can_edit_other_admins_post(self):
        """test an admin user can edit another admin users post"""
        another_admin_user = User.objects.create(
            first_name='Second_admin',
            email="second_admin@example.com",
            is_staff=True,
        )
        self.client.force_authenticate(another_admin_user)
        payload = {"body": "this is an update"}
        res = self.client.patch(post_detail_url(self.blog_post.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_list_all_comments_from_all_users(self):
        """test all users comments are visiable and listed"""

        another_regular_user = User.objects.create(
            first_name='jess', email="jesspearson@example.com"
        )
        create_comment(user=self.regular_user, post=self.blog_post)
        create_comment(user=another_regular_user, post=self.blog_post)

        res = self.client.get(COMMENT_URL)

        comment = Comment.objects.all().order_by("-id")
        serializer = CommentSerializer(comment, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_list_all_posts(self):
        """test all admin posts are visible and listed"""
        another_admin_user = User.objects.create(
            first_name='Second_admin',
            email="second_admin@example.com",
            is_staff=True,
        )
        create_blog_post(user=self.admin_user)
        create_blog_post(user=another_admin_user)

        res = self.client.get(POST_URL)

        post = Post.objects.all().order_by("-id")
        serializer = PostSerializer(post, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    # def setUp(self):
    #     self.client = APIClient()
    #     self.user = get_user_model().objects.create_user(
    #         'user@example.com',
    #         'password123',
    #     )
    #     self.client.force_authenticate(self.user)
    #     self.post = create_product(user=self.user)

    # def tearDown(self):
    #     self.post.image.delete()
