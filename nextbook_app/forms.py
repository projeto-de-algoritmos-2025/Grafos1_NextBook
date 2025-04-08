from django import forms
from .models import Avaliacao, Comentario

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