from django import forms
from .models import  Livro


class FavoritarLivroForm(forms.Form):
    livro = forms.ModelChoiceField(queryset=Livro.objects.all())

from django import forms
from django.contrib.auth.models import User

class CadastroForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password', 'email']
