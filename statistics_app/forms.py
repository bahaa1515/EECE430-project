from django import forms

from players.models import Player

from .models import PlayerStat


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
