from django.db import models
from django.conf import settings
from django.utils.text import slugify


class LivroTitulo(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    dt_publicacao = models.DateField()
    sinopse = models.TextField()
    capaPath = models.CharField(max_length=100, blank=True, null=True)
    avaliacao = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo


class Livro(models.Model):
    id_livro = models.AutoField(primary_key=True)
    titulo = models.OneToOneField(LivroTitulo, on_delete=models.CASCADE)
    autor = models.CharField(max_length=100)
    editora = models.CharField(max_length=100, blank=True)
    num_paginas = models.IntegerField()

    def __str__(self):
        return f"Livro: {self.titulo.titulo}"


class GeneroLivro(models.Model):
    id = models.AutoField(primary_key=True)
    nome_genero = models.CharField(max_length=50)

    def __str__(self):
        return self.nome_genero


class PossuiGeneroLivro(models.Model):
    titulo = models.ForeignKey(LivroTitulo, on_delete=models.RESTRICT)
    genero = models.ForeignKey(GeneroLivro, on_delete=models.RESTRICT)


class PrefereGeneroLivro(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    genero = models.ForeignKey(GeneroLivro, on_delete=models.RESTRICT)


class LivroFavorito(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    titulo = models.ForeignKey(LivroTitulo, on_delete=models.SET_NULL, null=True)
