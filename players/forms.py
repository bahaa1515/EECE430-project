from django import forms
from django.db import transaction

from accounts.models import CustomUser
from .models import Player

PLAYER_EMAIL_DOMAIN = "@mail.aub.edu"

_STAT_WIDGETS = {
    "jersey_number": forms.NumberInput(attrs={"class": "form-input", "min": 0, "max": 99}),
    "position": forms.Select(attrs={"class": "form-select"}),
    "player_type": forms.Select(attrs={"class": "form-select"}),
    "photo": forms.ClearableFileInput(attrs={"class": "form-input"}),
    "points": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
    "kills": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
    "blocks": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
    "aces": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
    "digs": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
    "assists": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
    "attack_pct": forms.NumberInput(attrs={"class": "form-input", "min": 0, "max": 100}),
    "perfect_recv_pct": forms.NumberInput(attrs={"class": "form-input", "min": 0, "max": 100}),
    "is_active": forms.CheckboxInput(),
}


class PlayerCreateForm(forms.ModelForm):
    """Manager/coach adds a new player. Creates the CustomUser account inline."""

    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "First name"}),
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Last name"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-input", "placeholder": "player@mail.aub.edu"}),
        help_text=f"Must end in {PLAYER_EMAIL_DOMAIN}",
    )
    password = forms.CharField(
        required=True,
        label="Password",
        min_length=6,
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Minimum 6 characters"}),
    )
    password_confirm = forms.CharField(
        required=True,
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Repeat password"}),
    )

    class Meta:
        model = Player
        fields = [
            "jersey_number", "position", "player_type", "photo",
            "points", "kills", "blocks", "aces", "digs", "assists",
            "attack_pct", "perfect_recv_pct", "is_active",
        ]
        widgets = _STAT_WIDGETS

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if not email.endswith(PLAYER_EMAIL_DOMAIN):
            raise forms.ValidationError(f"Player email must end in {PLAYER_EMAIL_DOMAIN}.")
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("password_confirm"):
            self.add_error("password_confirm", "Passwords do not match.")
        if cleaned_data.get("player_type") == Player.TYPE_STARTING and cleaned_data.get("is_active"):
            if Player.active_starters().count() >= Player.MAX_STARTERS:
                self.add_error(
                    "player_type",
                    f"Only {Player.MAX_STARTERS} active starters are allowed. "
                    "Demote or swap a current starter first.",
                )
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        first_name = self.cleaned_data["first_name"].strip()
        last_name  = self.cleaned_data["last_name"].strip()
        email      = self.cleaned_data["email"]
        password   = self.cleaned_data["password"]

        base = email.split("@")[0]
        username = base
        counter = 2
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1

        user = CustomUser.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name,
            role=CustomUser.ROLE_PLAYER,
        )
        player = super().save(commit=False)
        player.name = f"{first_name} {last_name}"
        player.user = user
        if commit:
            player.save()
        return player


class PlayerEditForm(forms.ModelForm):
    """Edit an existing player — no account creation fields."""

    class Meta:
        model = Player
        fields = [
            "name", "jersey_number", "position", "player_type", "photo",
            "points", "kills", "blocks", "aces", "digs", "assists",
            "attack_pct", "perfect_recv_pct", "is_active",
        ]
        widgets = {"name": forms.TextInput(attrs={"class": "form-input"}), **_STAT_WIDGETS}

    def clean_jersey_number(self):
        n = self.cleaned_data["jersey_number"]
        qs = Player.objects.filter(jersey_number=n, is_active=True)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("An active player already uses this jersey number.")
        return n

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("player_type") == Player.TYPE_STARTING and cleaned_data.get("is_active"):
            starters = Player.active_starters()
            if self.instance.pk:
                starters = starters.exclude(pk=self.instance.pk)
            if starters.count() >= Player.MAX_STARTERS:
                self.add_error(
                    "player_type",
                    f"Only {Player.MAX_STARTERS} active starters are allowed. "
                    "Demote or swap a current starter first.",
                )
        return cleaned_data


class SwapStarterForm(forms.Form):
    replacement = forms.ModelChoiceField(
        queryset=Player.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Substitute to promote",
    )

    def __init__(self, *args, starter=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Player.objects.filter(
            player_type=Player.TYPE_SUBSTITUTE, is_active=True
        ).order_by("jersey_number", "name")
        if starter is not None:
            qs = qs.exclude(pk=starter.pk)
        self.fields["replacement"].queryset = qs