
"""Serializers for the news application's REST API."""

from rest_framework import serializers

from .models import Article, CustomUser, Newsletter, Publisher


class CustomUserSerializer(serializers.ModelSerializer):
    """Convert user information into API data."""

    class Meta:
        model = CustomUser
        fields = [  # noqa: RUF012
            "id",
            "username",
            "email",
            "role",
        ]
        read_only_fields = ["id"]  # noqa: RUF012


class PublisherSerializer(serializers.ModelSerializer):
    """Convert publisher information into API data."""

    class Meta:
        model = Publisher
        fields = [  # noqa: RUF012
            "id",
            "name",
            "description",
            "editors",
            "journalists",
        ]
        read_only_fields = ["id"]  # noqa: RUF012


class ArticleSerializer(serializers.ModelSerializer):
    """Convert article information into API data."""

    class Meta:
        model = Article
        fields = [  # noqa: RUF012
            "id",
            "title",
            "content",
            "author",
            "publisher",
            "created_at",
            "approved",
        ]
        read_only_fields = ["id", "created_at", "approved"]  # noqa: RUF012


class NewsletterSerializer(serializers.ModelSerializer):
    """Convert newsletter information into API data."""

    class Meta:
        model = Newsletter
        fields = [  # noqa: RUF012
            "id",
            "title",
            "description",
            "created_at",
            "author",
            "articles",
        ]
        read_only_fields = ["id", "created_at"]  # noqa: RUF012
