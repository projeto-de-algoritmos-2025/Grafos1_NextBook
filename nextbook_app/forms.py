from django import forms
from .models import Avaliacao, Comentario, Livro

class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        fields = ['classificacao']
        labels = {
            'classificacao': 'Sua avaliação',
        }

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['texto']
        labels = {
            'texto': 'Seu comentário',
        }

class FavoritarLivroForm(forms.Form):
    livro = forms.ModelChoiceField(queryset=Livro.objects.all())