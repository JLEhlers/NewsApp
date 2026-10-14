from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Model representing a user of the news application.

    Fields:
    - role: The user's role in the application.
    - publisher_subscriptions: Publishers followed by readers.
    - journalist_subscriptions: Journalists followed by readers.
    """

    ROLE_CHOICES = [  # noqa: RUF012
        ("reader", "Reader"),
        ("editor", "Editor"),
        ("journalist", "Journalist"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="reader"
    )

    publisher_subscriptions = models.ManyToManyField(
        "Publisher",
        blank=True,
        related_name="subscribers"
    )

    journalist_subscriptions = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="journalist_subscribers",
        limit_choices_to={"role": "journalist"}
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class Publisher(models.Model):
    """
    Model representing a news publisher.

    Fields:
    - name: The publisher's name.
    - description: Information about the publisher.
    - editors: Editors who work for the publisher.
    - journalists: Journalists who work for the publisher.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="edited_publishers",
        limit_choices_to={"role": "editor"}
    )

    journalists = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="journalist_publishers",
        limit_choices_to={"role": "journalist"}
    )

    def __str__(self):
        return self.name


class Article(models.Model):
    """
    Model representing a news article.

    Fields:
    - title: The article's title.
    - content: The article's full content.
    - author: The independent journalist who wrote the article.
    - publisher: The publisher responsible for the article.
    - created_at: The date and time the article was created.
    - approved: Whether an editor has approved the article.

    Each article must have either an author or a publisher,
    but not both.
    """

    title = models.CharField(max_length=255)
    content = models.TextField()

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="independent_articles",
        limit_choices_to={"role": "journalist"}
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="articles"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=(
                    models.Q(
                        author__isnull=False,
                        publisher__isnull=True
                    )
                    | models.Q(
                        author__isnull=True,
                        publisher__isnull=False
                    )
                ),
                name="article_has_author_or_publisher"
            )
        ]


class Newsletter(models.Model):
    """
    Model representing a newsletter containing selected articles.

    Fields:
    - title: The newsletter's title.
    - description: A description of the newsletter.
    - created_at: The date and time the newsletter was created.
    - author: The journalist who created the newsletter.
    - articles: Articles included in the newsletter.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="newsletters",
        limit_choices_to={"role": "journalist"}
    )

    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name="newsletters"
    )

    def __str__(self):
        return self.title
