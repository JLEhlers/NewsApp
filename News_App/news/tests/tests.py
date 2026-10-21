
"""Automated tests for the News App REST API."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from news.models import Article, Newsletter, Publisher
from news.serializers import (
    CustomUserSerializer,
    NewsletterSerializer,
    PublisherSerializer,
)

User = get_user_model()


class NewsAPITests(APITestCase):
    """Test API authentication, permissions and article subscriptions."""

    def setUp(self):
        """Create test users and sample news content."""

        self.reader = User.objects.create_user(
            username="test_reader",
            password="TestPassword123!",
            email="reader@example.com",
            role="reader",
        )

        self.journalist = User.objects.create_user(
            username="test_journalist",
            password="TestPassword123!",
            email="journalist@example.com",
            role="journalist",
        )

        self.other_journalist = User.objects.create_user(
            username="other_journalist",
            password="TestPassword123!",
            email="other_journalist@example.com",
            role="journalist",
        )

        self.editor = User.objects.create_user(
            username="test_editor",
            password="TestPassword123!",
            role="editor",
        )

        self.publisher = Publisher.objects.create(
            name="Test Publisher",
            description="A test news publisher.",
        )

        self.other_publisher = Publisher.objects.create(
            name="Other Publisher",
            description="Another test publisher.",
        )

        # Approved article from a journalist.
        self.journalist_article = Article.objects.create(
            title="Journalist News",
            content="News written by a journalist.",
            author=self.journalist,
            publisher=None,
            approved=True,
        )

        # Approved article from a publisher.
        self.publisher_article = Article.objects.create(
            title="Publisher News",
            content="News from a publisher.",
            author=None,
            publisher=self.publisher,
            approved=True,
        )

        # Approved article from a journalist the reader does not follow.
        self.unsubscribed_article = Article.objects.create(
            title="Unsubscribed News",
            content="The reader has not subscribed to this journalist.",
            author=self.other_journalist,
            publisher=None,
            approved=True,
        )

        # An unapproved article must not appear in public results.
        self.unapproved_article = Article.objects.create(
            title="Unapproved News",
            content="This article is awaiting approval.",
            author=self.journalist,
            publisher=None,
            approved=False,
        )

        # Subscribe the reader to one journalist and one publisher.
        self.reader.journalist_subscriptions.add(self.journalist)
        self.reader.publisher_subscriptions.add(self.publisher)

        self.client = APIClient()

    def authenticate(self, user):
        """Authenticate an API request as the supplied user."""
        self.client.force_authenticate(user=user)

    def test_unauthenticated_request_is_rejected(self):
        """An unauthenticated client cannot access protected API views."""

        response = self.client.get(reverse("api_article_list"))

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_reader_can_retrieve_approved_articles(self):
        """Readers can retrieve approved articles."""

        self.authenticate(self.reader)

        response = self.client.get(reverse("api_article_list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = [item["id"] for item in response.data]

        self.assertIn(self.journalist_article.id, returned_ids)
        self.assertIn(self.publisher_article.id, returned_ids)
        self.assertNotIn(self.unapproved_article.id, returned_ids)

    def test_reader_only_receives_subscribed_articles(self):
        """Subscribed results contain only followed sources."""

        self.authenticate(self.reader)

        response = self.client.get(
            reverse("api_subscribed_articles")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = [item["id"] for item in response.data]

        self.assertIn(self.journalist_article.id, returned_ids)
        self.assertIn(self.publisher_article.id, returned_ids)
        self.assertNotIn(self.unsubscribed_article.id, returned_ids)
        self.assertNotIn(self.unapproved_article.id, returned_ids)

    def test_journalist_can_create_article(self):
        """A journalist can create an unapproved article."""

        self.authenticate(self.journalist)

        response = self.client.post(
            reverse("api_article_list"),
            {
                "title": "New Article",
                "content": "Content for a new article.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        article = Article.objects.get(title="New Article")

        self.assertEqual(article.author, self.journalist)
        self.assertIsNone(article.publisher)
        self.assertFalse(article.approved)

    def test_reader_cannot_create_article(self):
        """A reader cannot create articles."""

        self.authenticate(self.reader)

        response = self.client.post(
            reverse("api_article_list"),
            {
                "title": "Reader Article",
                "content": "A reader should not create this.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_client_can_retrieve_single_approved_article(self):
        """An individual approved article can be retrieved."""

        self.authenticate(self.reader)

        response = self.client.get(
            reverse(
                "api_article_detail",
                args=[self.journalist_article.id],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["title"],
            "Journalist News",
        )

    def test_missing_article_returns_404(self):
        """Requesting an article that does not exist returns 404."""

        self.authenticate(self.reader)

        response = self.client.get(
            reverse("api_article_detail", args=[999999])
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_editor_can_delete_article(self):
        """An editor can delete an article."""

        self.authenticate(self.editor)

        response = self.client.delete(
            reverse(
                "api_article_detail",
                args=[self.journalist_article.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Article.objects.filter(
                id=self.journalist_article.id
            ).exists()
        )

    def test_reader_cannot_delete_article(self):
        """A reader cannot delete an article."""

        self.authenticate(self.reader)

        response = self.client.delete(
            reverse(
                "api_article_detail",
                args=[self.journalist_article.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            Article.objects.filter(
                id=self.journalist_article.id
            ).exists()
        )

    def test_token_endpoint_returns_token(self):
        """Valid credentials can obtain an API token."""

        response = self.client.post(
            reverse("api_token"),
            {
                "username": "test_reader",
                "password": "TestPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

        self.assertTrue(
            Token.objects.filter(user=self.reader).exists()
        )

    def test_newsletter_serializer(self):
        """A newsletter serializes its author and selected articles."""

        newsletter = Newsletter.objects.create(
            title="Weekly News",
            description="A collection of weekly articles.",
            author=self.journalist,
        )
        newsletter.articles.add(self.journalist_article)

        data = NewsletterSerializer(newsletter).data

        self.assertEqual(data["title"], "Weekly News")
        self.assertEqual(data["author"], self.journalist.id)
        self.assertIn(
            self.journalist_article.id,
            data["articles"],
        )

    def test_publisher_serializer(self):
        """A publisher serializes its basic information."""

        data = PublisherSerializer(self.publisher).data

        self.assertEqual(data["name"], "Test Publisher")

    def test_user_serializer(self):
        """A user serializes without exposing their password."""

        data = CustomUserSerializer(self.reader).data

        self.assertEqual(data["username"], "test_reader")
        self.assertEqual(data["role"], "reader")
        self.assertNotIn("password", data)

    @patch("news.views.requests.post")
    @patch("news.views.send_mail")
    def test_editor_approval_sends_email_and_api_request(
        self,
        mock_send_mail,
        mock_requests_post,
    ):
        """Approving an article triggers email and API integration."""

        # Make this test use a reader subscribed to the journalist.
        self.reader.journalist_subscriptions.add(self.journalist)

        # Use a fresh, unapproved article for this test.
        article = self.unapproved_article

        # A normal Django view uses session login, not force_authenticate.
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse("approve_article", args=[article.id])
        )

        self.assertTrue(
            Article.objects.get(id=article.id).approved
        )

        self.assertTrue(mock_send_mail.called)
        self.assertTrue(mock_requests_post.called)

        # The approval view may redirect after processing.
        self.assertIn(response.status_code, [200, 302])

    def test_unapproved_article_is_rejected_by_approval_api(self):
        """The approval integration rejects unapproved articles."""

        self.authenticate(self.editor)

        response = self.client.post(
            reverse("api-approved"),
            {"article_id": self.unapproved_article.id},
            format="json",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_403_FORBIDDEN,
            ],
        )
