from django import forms
from django.utils import timezone

from .models import Match


class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = [
            "title",
            "match_type",
            "status",
            "date",
            "duration_hours",
            "location",
            "confirmation_closes",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Match or practice title"}
            ),
            "match_type": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateTimeInput(
                attrs={"class": "form-input", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "duration_hours": forms.NumberInput(
                attrs={"class": "form-input", "min": 1, "max": 8}
            ),
            "location": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Charles Hostler"}
            ),
            "confirmation_closes": forms.DateTimeInput(
                attrs={"class": "form-input", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("date", "confirmation_closes"):
            value = self.initial.get(field_name) or getattr(self.instance, field_name, None)
            if value:
                local_value = timezone.localtime(value)
                self.initial[field_name] = local_value.strftime("%Y-%m-%dT%H:%M")

    def clean(self):
        cleaned_data = super().clean()
        match_date = cleaned_data.get("date")
        closes = cleaned_data.get("confirmation_closes")

        if closes and match_date and closes > match_date:
            self.add_error(
                "confirmation_closes",
                "Confirmation must close before the scheduled match time.",
            )

        return cleaned_data
