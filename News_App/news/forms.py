"""Forms for the news application."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser, Publisher

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Form for creating a user with a selected role."""

    class Meta:
        model = CustomUser
        fields = ("username", "role", "email")
        email = forms.EmailField(required=True)


class PublisherForm(forms.ModelForm):
    """Form for creating publishers and assigning their staff."""

    editors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role="editor"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    journalists = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role="journalist"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Publisher
        fields = ["name", "description", "editors", "journalists"]
