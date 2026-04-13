from django import forms

from attendance.models import Match
from players.models import Player

from .models import MVP, MatchHighlight


class MatchHighlightForm(forms.ModelForm):
    class Meta:
        model = MatchHighlight
        fields = ["session", "title", "score", "summary", "image"]
        widgets = {
            "session": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Highlight title"}
            ),
            "score": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Score (e.g. 3-2)"}
            ),
            "summary": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "rows": 4,
                    "placeholder": "Summarize what happened in this match.",
                }
            ),
            "image": forms.ClearableFileInput(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["session"].queryset = Match.objects.order_by("-date")
        self.fields["session"].empty_label = "Select match / practice"
        self.fields["session"].required = True


class MVPForm(forms.ModelForm):
    class Meta:
        model = MVP
        fields = [
            "session",
            "player",
            "points",
            "points_per_match",
            "attack_success_rate",
            "blocks",
        ]
        widgets = {
            "session": forms.Select(attrs={"class": "form-select"}),
            "player": forms.Select(attrs={"class": "form-select"}),
            "points": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "points_per_match": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "step": "0.1"}
            ),
            "attack_success_rate": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "max": 100}
            ),
            "blocks": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["session"].queryset = Match.objects.order_by("-date")
        self.fields["session"].empty_label = "Select match / practice"
        self.fields["session"].required = True
        self.fields["player"].queryset = Player.objects.filter(is_active=True).order_by("name")
