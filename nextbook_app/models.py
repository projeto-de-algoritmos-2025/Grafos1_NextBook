from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class Genero(models.Model):
    """Modelo para categorias/gêneros de livros"""
    nome = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Gênero"
        verbose_name_plural = "Gêneros"
        ordering = ['nome']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

class Titulo(models.Model):
    nome = models.CharField(max_length=200)

    def __str__(self):
        return self.nome

class Livro(models.Model):
    """Modelo principal para livros, integrado com a API do Google Books"""
    id = models.CharField(primary_key=True, max_length=255)  # Usando como primary key
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    autores = models.TextField(help_text="Nomes dos autores separados por vírgula")
    descricao = models.TextField(blank=True, null=True)
    editora = models.CharField(max_length=100, blank=True, null=True)
    data_publicacao = models.DateField(blank=True, null=True)
    capa_url = models.URLField(max_length=500, blank=True, null=True)
    capa = models.ImageField(upload_to='livros/', blank=True, null=True)  # Campo renomeado
    idioma = models.CharField(max_length=10, blank=True, null=True)
    isbn = models.CharField(max_length=20, blank=True, null=True)
    avaliacao_media = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Livro"
        verbose_name_plural = "Livros"
        ordering = ['-criado_em']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.titulo)
            self.slug = base_slug
            counter = 1
            while Livro.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

    @property
    def lista_autores(self):
        """Retorna uma lista de autores"""
        return [autor.strip() for autor in self.autores.split(',')]

    @property
    def capa_thumbnail(self):
        if self.capa_url:
            return self.capa_url
        return '/static/imgs/book-placeholder.png'


class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    livros_favoritos = models.ManyToManyField(Livro, related_name='favorito_por', blank=True)

    def __str__(self):
        return self.user.username


class Favorito(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    livro = models.ForeignKey('Livro', on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'livro')
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'

    def __str__(self):
        return f"{self.usuario.username} - {self.livro.titulo}"

class Prefere(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    genero = models.ForeignKey(Genero, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)

class GrafoLivros(models.Model):
    livro_origem = models.ForeignKey('Livro', related_name='recomendacoes_feitas', on_delete=models.CASCADE)
    livro_destino = models.ForeignKey('Livro', related_name='recomendacoes_recebidas', on_delete=models.CASCADE)
    peso = models.IntegerField(default=1)  # Pode representar força da conexão

    class Meta:
        unique_together = ('livro_origem', 'livro_destino')