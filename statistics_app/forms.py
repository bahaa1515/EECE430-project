from django import forms

from attendance.models import Match
from players.models import Player

from .models import PlayerStat, SessionStat


class PlayerStatForm(forms.ModelForm):
    class Meta:
        model = PlayerStat
        fields = ["player", "date", "opponent", "kills", "blocks", "aces", "mvp"]
        widgets = {
            "player": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "opponent": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Opponent or session name"}
            ),
            "kills": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "blocks": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "aces": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "mvp": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["player"].queryset = Player.objects.filter(is_active=True).order_by("name")


class SessionStatForm(forms.ModelForm):
    class Meta:
        model = SessionStat
        fields = [
            "match",
            "team_score",
            "opponent_score",
            "sets_won",
            "sets_lost",
            "kills",
            "blocks",
            "aces",
            "notes",
        ]
        widgets = {
            "match": forms.Select(attrs={"class": "form-select"}),
            "team_score": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "opponent_score": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "sets_won": forms.NumberInput(attrs={"class": "form-input", "min": 0, "max": 5}),
            "sets_lost": forms.NumberInput(attrs={"class": "form-input", "min": 0, "max": 5}),
            "kills": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "blocks": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "aces": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "rows": 4,
                    "placeholder": "Optional summary of what happened in this session.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["match"].queryset = Match.objects.order_by("-date", "title")

    def clean_match(self):
        match = self.cleaned_data["match"]
        existing = SessionStat.objects.filter(match=match)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError(
                "Session stats already exist for this session. Open the existing report to edit it."
            )
        return match
