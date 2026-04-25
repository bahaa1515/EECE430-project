from datetime import timedelta

from django import forms
from django.utils import timezone

from .models import Match


HOME_VENUE = "Charles Hostler"


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
                attrs={
                    "class": "form-input",
                    "placeholder": "Charles Hostler or away university stadium",
                    "list": "venue-options",
                }
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
            if value and not isinstance(value, str):
                local_value = timezone.localtime(value)
                self.initial[field_name] = local_value.strftime("%Y-%m-%dT%H:%M")

    def clean(self):
        cleaned_data = super().clean()
        match_date = cleaned_data.get("date")
        closes = cleaned_data.get("confirmation_closes")
        duration_hours = cleaned_data.get("duration_hours")
        match_type = cleaned_data.get("match_type")
        status = cleaned_data.get("status")
        location = (cleaned_data.get("location") or "").strip()

        if location.lower() == HOME_VENUE.lower():
            location = HOME_VENUE
            cleaned_data["location"] = HOME_VENUE

        if match_type == Match.TYPE_PRACTICE and location != HOME_VENUE:
            self.add_error(
                "location",
                "Practice sessions can only be scheduled at Charles Hostler.",
            )

        if location and location != HOME_VENUE and match_type != Match.TYPE_MATCH:
            self.add_error(
                "match_type",
                "Away university venues can only be used for matches.",
            )

        if closes and match_date and closes > match_date:
            self.add_error(
                "confirmation_closes",
                "Confirmation must close before the scheduled match time.",
            )

        if match_date and duration_hours and status != Match.STATUS_CANCELLED:
            new_end = match_date + timedelta(hours=duration_hours)
            existing_sessions = Match.objects.exclude(status=Match.STATUS_CANCELLED)
            if self.instance.pk:
                existing_sessions = existing_sessions.exclude(pk=self.instance.pk)

            for existing in existing_sessions:
                existing_end = existing.date + timedelta(hours=existing.duration_hours)
                if match_date < existing_end and new_end > existing.date:
                    self.add_error(
                        "date",
                        (
                            f"This session overlaps with {existing.title} "
                            f"({timezone.localtime(existing.date).strftime('%b %d, %I:%M %p')})."
                        ),
                    )
                    break

        return cleaned_data
