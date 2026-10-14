"""Forms for the news application."""

from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Form for creating a user with a selected role."""

    class Meta:
        model = CustomUser
        fields = ("username", "role")
