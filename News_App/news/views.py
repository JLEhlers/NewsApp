
"""Views for the news application."""

from functools import wraps

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .forms import CustomUserCreationForm
from .models import Article, Newsletter, Publisher
from .serializers import (
    ArticleSerializer,
)

User = get_user_model()


# Restrict views to users with the required role.

def role_required(role):
    """Allow access to users with a role or matching Django group."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")

            has_role = request.user.role == role
            has_group = request.user.groups.filter(
                name="Editor"
            ).exists()

            if has_role or (role == "editor" and has_group):
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden(
                "You do not have permission to access this page."
            )

        return wrapper
    return decorator


# Display the correct dashboard.

@login_required
def dashboard(request):
    """Display a dashboard based on the user's role."""

    if request.user.role == "reader":
        return render(request, "news/reader_dashboard.html")

    if request.user.role == "editor":
        return render(request, "news/editor_dashboard.html")

    if request.user.role == "journalist":
        return render(request, "news/journalist_dashboard.html")

    return HttpResponseForbidden("Invalid user role.")


# Register a new user.

def register(request):
    """Register a new user and allow them to select a role."""

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Your account has been created. You can now log in."
            )
            return redirect("login")
    else:
        form = CustomUserCreationForm()

    return render(
        request,
        "news/register.html",
        {
            "form": form,
            "role_choices": CustomUserCreationForm(
            ).fields["role"].choices,
        },
    )


# Display approved articles.

def article_list(request):
    """Display all approved articles."""

    articles = Article.objects.filter(approved=True).order_by(
        "-created_at"
    )

    return render(
        request,
        "news/article_list.html",
        {"articles": articles},
    )


# Display approved article.

def article_detail(request, article_id):
    """Display approved article."""

    article = get_object_or_404(
        Article,
        id=article_id,
        approved=True,
    )

    return render(
        request,
        "news/article_detail.html",
        {"article": article},
    )


# Display newsletters.

def newsletter_list(request):
    """Display newsletters to readers and other users."""

    newsletters = Newsletter.objects.all().order_by("-created_at")

    return render(
        request,
        "news/newsletter_list.html",
        {"newsletters": newsletters},
    )


# Display a newsletter and its articles.

def newsletter_detail(request, newsletter_id):
    """Display a newsletter and its articles."""

    newsletter = get_object_or_404(
        Newsletter,
        id=newsletter_id,
    )

    return render(
        request,
        "news/newsletter_detail.html",
        {"newsletter": newsletter},
    )


# Allow journalists to create independent articles.

@login_required
@role_required("journalist")
def create_article(request):
    """Create an article written by the logged-in journalist."""

    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")

        if not title or not content:
            messages.error(request, "Enter a title and content.")
        else:
            Article.objects.create(
                title=title,
                content=content,
                author=request.user,
                publisher=None,
                approved=False,
            )

            messages.success(
                request,
                "Article created and submitted for approval.",
            )
            return redirect("article_list")

    return render(request, "news/article_form.html")


# Allow editors to review and approve articles.

@login_required
@role_required("editor")
def review_articles(request):
    """Display articles awaiting editorial approval."""

    articles = Article.objects.filter(
        approved=False
    ).order_by("-created_at")

    return render(
        request,
        "news/review_articles.html",
        {"articles": articles},
    )


@login_required
@role_required("editor")
def approve_article(request, article_id):
    """Approve an article, email subscribers, and call the API."""

    if request.method != "POST":
        return HttpResponseForbidden("Use POST to approve articles.")

    article = get_object_or_404(Article, id=article_id)

    if article.approved:
        messages.info(request, "This article is already approved.")
        return redirect("review_articles")

    article.approved = True
    article.save(update_fields=["approved"])

    # Find readers subscribed to this journalist or publisher.
    subscribers = User.objects.filter(role="reader")

    if article.author_id:
        subscribers = subscribers.filter(
            journalist_subscriptions=article.author
        )

    elif article.publisher_id:
        subscribers = subscribers.filter(
            publisher_subscriptions=article.publisher
        )

    email_addresses = list(
        subscribers.exclude(email="").values_list("email", flat=True)
    )

    if email_addresses:
        send_mail(
            subject=f"New article: {article.title}",
            message=(
                f"A new article has been approved.\n\n"
                f"{article.title}\n\n{article.content}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=email_addresses,
            fail_silently=False,
        )

    # Send a POST request to the application's own API endpoint.
    api_url = request.build_absolute_uri(
        reverse("api-approved")
    )

    try:
        requests.post(
            api_url,
            json={"article_id": article.id},
            timeout=5,
        ).raise_for_status()
    except requests.RequestException:
        # The article remains approved if the API call fails.
        messages.warning(
            request,
            "The article was approved, but API sharing failed.",
        )
    else:
        messages.success(
            request,
            "Article approved and shared successfully.",
        )

    return redirect("review_articles")


# REST API: list articles and create articles.

@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_article_list(request):
    """List approved articles or allow journalists to create articles."""

    if request.method == "GET":
        articles = Article.objects.filter(approved=True).order_by(
            "-created_at"
        )
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

    # POST requests are only allowed for journalists.
    if request.user.role != "journalist":
        return Response(
            {"error": "Only journalists can create articles."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = ArticleSerializer(data=request.data)

    if serializer.is_valid():
        article = serializer.save(
            author=request.user,
            publisher=None,
            approved=False,
        )

        return Response(
            ArticleSerializer(article).data,
            status=status.HTTP_201_CREATED,
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST,
    )


# REST API: retrieve, update, or delete one article.

@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_article_detail(request, article_id):
    """Retrieve, update, or delete an article according to user role."""

    article = get_object_or_404(Article, id=article_id)

    # Readers can only view approved articles.
    if request.method == "GET":
        if not article.approved and request.user.role == "reader":
            return Response(
                {"error": "This article has not been approved."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ArticleSerializer(article)
        return Response(serializer.data)

    # Only editors and journalists may update or delete.
    if request.user.role not in ["editor", "journalist"]:
        return Response(
            {"error": "You do not have permission to change articles."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Journalists may only change their own independent articles.
    if (
        request.user.role == "journalist"
        and article.author_id != request.user.id
    ):
        return Response(
            {"error": "You can only change your own articles."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Update the article.
    if request.method == "PUT":
        serializer = ArticleSerializer(
            article,
            data=request.data,
        )

        if serializer.is_valid():
            serializer.save(
                author=article.author,
                publisher=article.publisher,
                approved=article.approved,
            )
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Delete the article.
    article.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)


# REST API: retrieve articles from a reader's subscriptions.
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_subscribed_articles(request):
    """Return approved articles from the reader's subscriptions."""

    # Only readers can access their subscribed articles.
    if request.user.role != "reader":
        return Response(
            {"error": "Only readers can view subscribed articles."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Find articles from subscribed publishers.
    publisher_articles = Article.objects.filter(
        approved=True,
        publisher__in=request.user.publisher_subscriptions.all(),
    )

    # Find articles from subscribed journalists.
    journalist_articles = Article.objects.filter(
        approved=True,
        author__in=request.user.journalist_subscriptions.all(),
    )

    # Combine both lists without duplicates.
    articles = (
        publisher_articles | journalist_articles
    ).distinct().order_by("-created_at")

    serializer = ArticleSerializer(articles, many=True)

    return Response(serializer.data)


# API endpoint called after an article is approved.

@api_view(["POST"])
def api_approved(request):
    """Record an article approval integration request."""

    article_id = request.data.get("article_id")

    if not article_id:
        return Response(
            {"error": "Article ID is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    article = get_object_or_404(
        Article,
        id=article_id,
        approved=True,
    )

    return Response(
        {
            "message": "Approved article received by the API.",
            "article_id": article.id,
        },
        status=status.HTTP_200_OK,
    )


@login_required
def publisher_list(request):
    """Display publishers that readers can subscribe to."""
    publishers = Publisher.objects.all()

    subscribed_publisher_ids = []
    if request.user.role == "reader":
        subscribed_publisher_ids = list(
            request.user.publisher_subscriptions.values_list(
                "id", flat=True
            )
        )

    return render(
        request,
        "news/publisher_list.html",
        {
            "publishers": publishers,
            "subscribed_publisher_ids": subscribed_publisher_ids,
        },
    )


@login_required
def journalist_list(request):
    """Display journalists that readers can subscribe to."""
    journalists = User.objects.filter(role="journalist")

    subscribed_journalist_ids = []
    if request.user.role == "reader":
        subscribed_journalist_ids = list(
            request.user.journalist_subscriptions.values_list(
                "id", flat=True
            )
        )

    return render(
        request,
        "news/journalist_list.html",
        {
            "journalists": journalists,
            "subscribed_journalist_ids": subscribed_journalist_ids,
        },
    )


@login_required
def my_subscriptions(request):
    """Display the publishers and journalists a reader follows."""
    if request.user.role != "reader":
        return HttpResponseForbidden(
            "Only readers can view subscriptions."
        )

    return render(
        request,
        "news/my_subscriptions.html",
        {
            "publishers": request.user.publisher_subscriptions.all(),
            "journalists": request.user.journalist_subscriptions.all(),
        },
    )


@login_required
@require_POST
def subscribe_publisher(request, publisher_id):
    """Subscribe the current reader to a publisher."""
    if request.user.role != "reader":
        return HttpResponseForbidden("Only readers can subscribe.")

    publisher = get_object_or_404(Publisher, id=publisher_id)
    request.user.publisher_subscriptions.add(publisher)
    messages.success(request, f"You subscribed to {publisher.name}.")

    return redirect("publisher_list")


@login_required
@require_POST
def unsubscribe_publisher(request, publisher_id):
    """Unsubscribe the current reader from a publisher."""
    if request.user.role != "reader":
        return HttpResponseForbidden("Only readers can unsubscribe.")

    publisher = get_object_or_404(Publisher, id=publisher_id)
    request.user.publisher_subscriptions.remove(publisher)
    messages.success(request, f"You unsubscribed from {publisher.name}.")

    return redirect("publisher_list")


@login_required
@require_POST
def subscribe_journalist(request, journalist_id):
    """Subscribe the current reader to a journalist."""
    if request.user.role != "reader":
        return HttpResponseForbidden("Only readers can subscribe.")

    journalist = get_object_or_404(
        User, id=journalist_id, role="journalist"
    )
    request.user.journalist_subscriptions.add(journalist)
    messages.success(
        request, f"You subscribed to {journalist.username}."
    )

    return redirect("journalist_list")


@login_required
@require_POST
def unsubscribe_journalist(request, journalist_id):
    """Unsubscribe the current reader from a journalist."""
    if request.user.role != "reader":
        return HttpResponseForbidden("Only readers can unsubscribe.")

    journalist = get_object_or_404(
        User, id=journalist_id, role="journalist"
    )
    request.user.journalist_subscriptions.remove(journalist)
    messages.success(
        request, f"You unsubscribed from {journalist.username}."
    )

    return redirect("journalist_list")


# Edit an article.
@login_required
def edit_article(request, article_id):
    """Allow editors or the article's journalist to edit an article."""
    article = get_object_or_404(Article, id=article_id)

    is_editor = (
        request.user.role == "editor"
        or request.user.groups.filter(name="Editor").exists()
    )

    is_owner = article.author_id == request.user.id

    if not is_editor and not (
        request.user.role == "journalist" and is_owner
    ):
        return HttpResponseForbidden("You cannot edit this article.")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()

        if title and content:
            article.title = title
            article.content = content
            article.save()

            messages.success(request, "Article updated.")
            return redirect("dashboard")

        messages.error(request, "Enter a title and content.")

    return render(
        request,
        "news/article_form.html",
        {"article": article},
    )


# Delete an article.
@login_required
@require_POST
def delete_article(request, article_id):
    """Allow editors or the article's journalist to delete an article."""
    article = get_object_or_404(Article, id=article_id)

    is_editor = (
        request.user.role == "editor"
        or request.user.groups.filter(name="Editor").exists()
    )

    is_owner = article.author_id == request.user.id

    if not is_editor and not (
        request.user.role == "journalist" and is_owner
    ):
        return HttpResponseForbidden("You cannot delete this article.")

    article.delete()
    messages.success(request, "Article deleted.")
    return redirect("dashboard")


# Create a newsletter.
@login_required
def create_newsletter(request):
    """Allow journalists and editors to create newsletters."""
    is_editor = (
        request.user.role == "editor"
        or request.user.groups.filter(name="Editor").exists()
    )

    if request.user.role != "journalist" and not is_editor:
        return HttpResponseForbidden(
            "You cannot create newsletters."
        )

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        article_ids = request.POST.getlist("articles")

        if not title or not description:
            messages.error(request, "Enter a title and description.")
        else:
            newsletter = Newsletter.objects.create(
                title=title,
                description=description,
                author=request.user,
            )
            newsletter.articles.set(
                Article.objects.filter(id__in=article_ids)
            )

            messages.success(request, "Newsletter created.")
            return redirect("dashboard")

    return render(
        request,
        "news/newsletter_form.html",
        {
            "articles": Article.objects.filter(approved=True),
        },
    )


# Edit a newsletter.
@login_required
def edit_newsletter(request, newsletter_id):
    """Allow editors or the newsletter's journalist to edit it."""
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)

    is_editor = (
        request.user.role == "editor"
        or request.user.groups.filter(name="Editor").exists()
    )

    is_owner = newsletter.author_id == request.user.id

    if not is_editor and not (
        request.user.role == "journalist" and is_owner
    ):
        return HttpResponseForbidden("You cannot edit this newsletter.")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        article_ids = request.POST.getlist("articles")

        if title and description:
            newsletter.title = title
            newsletter.description = description
            newsletter.save()
            newsletter.articles.set(
                Article.objects.filter(id__in=article_ids)
            )

            messages.success(request, "Newsletter updated.")
            return redirect("dashboard")

        messages.error(request, "Enter a title and description.")

    return render(
        request,
        "news/newsletter_form.html",
        {
            "newsletter": newsletter,
            "articles": Article.objects.filter(approved=True),
            "selected_articles": newsletter.articles.all(),
        },
    )


# Delete a newsletter.
@login_required
@require_POST
def delete_newsletter(request, newsletter_id):
    """Allow editors or the newsletter's journalist to delete it."""
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)

    is_editor = (
        request.user.role == "editor"
        or request.user.groups.filter(name="Editor").exists()
    )

    is_owner = newsletter.author_id == request.user.id

    if not is_editor and not (
        request.user.role == "journalist" and is_owner
    ):
        return HttpResponseForbidden(
            "You cannot delete this newsletter."
        )

    newsletter.delete()
    messages.success(request, "Newsletter deleted.")
    return redirect("dashboard")
