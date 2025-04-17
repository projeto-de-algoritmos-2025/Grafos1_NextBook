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


class Perfil(models.Model):
    user= models.OneToOneField(User, on_delete=models.CASCADE)
    livros_favoritos = models.ManyToManyField('Livro', related_name='favorito_por', blank=True)


    def __str__(self):
        return self.user.username


class Favorito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    livro = models.ForeignKey("Livro", on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'livro')
        verbose_name_plural = 'Favoritos'

class Livro(models.Model):
    """Modelo principal para livros, integrado com a API do Google Books"""
    google_id = models.CharField(max_length=255, unique=True)
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    autor = models.CharField(max_length=200)
    autores = models.TextField(help_text="Nomes dos autores separados por vírgula")
    descricao = models.TextField(blank=True, null=True)
    editora = models.CharField(max_length=100, blank=True, null=True)
    data_publicacao = models.DateField(blank=True, null=True)
    paginas = models.PositiveIntegerField(blank=True, null=True)
    capa_url = models.URLField(max_length=500, blank=True, null=True)
    imagem = models.ImageField(upload_to='livros/')
    idioma = models.CharField(max_length=10, blank=True, null=True)
    isbn = models.CharField(max_length=20, blank=True, null=True, verbose_name="ISBN")
    avaliacao_media = models.FloatField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    contagem_avaliacoes = models.PositiveIntegerField(default=0)
    generos = models.ManyToManyField(Genero, related_name='livros', blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Livro"
        verbose_name_plural = "Livros"
        ordering = ['-criado_em']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

    @property
    def lista_autores(self):
        """Retorna uma lista de autores"""
        return [autor.strip() for autor in self.autores.split(',')]

    @property
    def lista_generos(self):
        """Retorna uma lista de gêneros"""
        return [genero.nome for genero in self.generos.all()]
