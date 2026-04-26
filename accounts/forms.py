from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'AUB username', 'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'AUB password', 'class': 'form-input'}))
    role = forms.ChoiceField(choices=[('player','Player'),('coach','Coach'),('manager','Manager')], widget=forms.HiddenInput())
    remember_me = forms.BooleanField(required=False)
