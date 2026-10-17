from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.article_list, name="article_list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("articles/<int:article_id>/",
         views.article_detail, name="article_detail"),
    path("articles/create/",
         views.create_article, name="create_article"),
    path("articles/review/",
         views.review_articles, name="review_articles"),
    path("articles/<int:article_id>/approve/",
         views.approve_article, name="approve_article"),
    path("newsletters/", views.newsletter_list, name="newsletter_list"),
    path("newsletters/<int:newsletter_id>/",
         views.newsletter_detail, name="newsletter_detail"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="news/login.html"
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    # REST API
    path("api/articles/",
         views.api_article_list, name="api_article_list"),
    path("api/articles/subscribed/",
         views.api_subscribed_articles, name="api_subscribed_articles"),
    path("api/articles/<int:article_id>/",
         views.api_article_detail, name="api_article_detail"),
    path("api/approved/",
         views.api_approved, name="api-approved"),
    path("publishers/", views.publisher_list, name="publisher_list"),
    path("journalists/", views.journalist_list, name="journalist_list"),
    path("subscriptions/", views.my_subscriptions, name="my_subscriptions"),

    path(
        "publishers/<int:publisher_id>/subscribe/",
        views.subscribe_publisher,
        name="subscribe_publisher",
    ),
    path(
        "publishers/<int:publisher_id>/unsubscribe/",
        views.unsubscribe_publisher,
        name="unsubscribe_publisher",
    ),
    path(
        "journalists/<int:journalist_id>/subscribe/",
        views.subscribe_journalist,
        name="subscribe_journalist",
    ),
    path(
        "journalists/<int:journalist_id>/unsubscribe/",
        views.unsubscribe_journalist,
        name="unsubscribe_journalist",
    ),
    path(
        "articles/<int:article_id>/edit/",
        views.edit_article,
        name="edit_article",
    ),
    path(
        "articles/<int:article_id>/delete/",
        views.delete_article,
        name="delete_article",
    ),
    path(
        "newsletters/create/",
        views.create_newsletter,
        name="create_newsletter",
    ),
    path(
        "newsletters/<int:newsletter_id>/edit/",
        views.edit_newsletter,
        name="edit_newsletter",
    ),
    path(
        "newsletters/<int:newsletter_id>/delete/",
        views.delete_newsletter,
        name="delete_newsletter",
    ),
]
