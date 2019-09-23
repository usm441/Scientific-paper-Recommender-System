from django.contrib.auth.models import User
from .models import Algorithm
from django.forms import ModelForm
from django import forms
from django.core.validators import RegexValidator


class UserForm(ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label='Initial Password* ')
    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 'is_active', 'is_superuser']
        labels = {'username': 'Username* '}


class AlgorithmsForm(ModelForm):
    def __init__(self, *args, **kwargs):
        validator = RegexValidator("\w{6}\-\w{2}", "CAPA format needs to be ######-##.")
        super(AlgorithmsForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['class'] = 'form-control spacing'
        self.fields['description'].widget.attrs['class'] = 'form-control spacing'
        self.fields['file'].widget.attrs['class'] = 'spacing'
    file = forms.FileField()

    class Meta:
        model = Algorithm
        fields = ['name', 'description', 'file']
        labels = {'name': 'Name', 'description':'Description', 'file':'File'}
