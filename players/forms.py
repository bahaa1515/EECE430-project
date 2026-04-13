from django import forms

from accounts.models import CustomUser

from .models import Player

STUDENT_EMAIL_DOMAIN = "@mail.aub.edu"


class PlayerForm(forms.ModelForm):
    user = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Student AUB email ending in @mail.aub.edu",
                "autocomplete": "off",
            }
        ),
        help_text="Required. Enter the player's student AUB email ending in @mail.aub.edu.",
    )

    class Meta:
        model = Player
        fields = [
            "name",
            "jersey_number",
            "position",
            "player_type",
            "user",
            "photo",
            "points",
            "kills",
            "blocks",
            "aces",
            "digs",
            "assists",
            "attack_pct",
            "perfect_recv_pct",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "jersey_number": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "max": 99}
            ),
            "position": forms.Select(attrs={"class": "form-select"}),
            "player_type": forms.Select(attrs={"class": "form-select"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-input"}),
            "points": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "kills": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "blocks": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "aces": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "digs": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "assists": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "attack_pct": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "max": 100}
            ),
            "perfect_recv_pct": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "max": 100}
            ),
            "is_active": forms.CheckboxInput(),
        }

    def clean_jersey_number(self):
        jersey_number = self.cleaned_data["jersey_number"]
        qs = Player.objects.filter(jersey_number=jersey_number, is_active=True)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "An active player already uses this jersey number."
            )
        return jersey_number

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.user_id:
            self.initial["user"] = self.instance.user.email

    def clean_user(self):
        email = (self.cleaned_data.get("user") or "").strip().lower()
        if not email:
            raise forms.ValidationError("A linked student account email is required.")
        if "@" not in email:
            raise forms.ValidationError("Enter the student's full AUB email address.")
        if not email.endswith(STUDENT_EMAIL_DOMAIN):
            raise forms.ValidationError(
                f"Linked players must use a student AUB email ending in {STUDENT_EMAIL_DOMAIN}."
            )

        try:
            user = CustomUser.objects.get(
                email__iexact=email,
                role=CustomUser.ROLE_STUDENT,
            )
        except CustomUser.DoesNotExist:
            raise forms.ValidationError(
                "No student account was found with that AUB email."
            )

        qs = Player.objects.filter(user=user)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This student account is already linked to a player.")
        return user

    def clean(self):
        cleaned_data = super().clean()
        player_type = cleaned_data.get("player_type")
        is_active = cleaned_data.get("is_active")

        if player_type == Player.TYPE_STARTING and is_active:
            starters = Player.active_starters()
            if self.instance.pk:
                starters = starters.exclude(pk=self.instance.pk)
            if starters.count() >= Player.MAX_STARTERS:
                self.add_error(
                    "player_type",
                    f"Only {Player.MAX_STARTERS} active starters are allowed. Demote or swap a current starter first.",
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
        self.fields["replacement"].queryset = Player.objects.filter(
            player_type=Player.TYPE_SUBSTITUTE,
            is_active=True,
        ).order_by("jersey_number", "name")
        if starter is not None:
            self.fields["replacement"].queryset = self.fields["replacement"].queryset.exclude(
                pk=starter.pk
            )
