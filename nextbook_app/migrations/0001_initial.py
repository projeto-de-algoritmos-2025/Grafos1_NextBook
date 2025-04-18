# Generated by Django 5.1.4 on 2025-04-18 16:40

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Genero",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nome", models.CharField(max_length=50, unique=True)),
                ("slug", models.SlugField(unique=True)),
            ],
            options={
                "verbose_name": "Gênero",
                "verbose_name_plural": "Gêneros",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="Titulo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nome", models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name="Livro",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("google_id", models.CharField(max_length=255, unique=True)),
                ("titulo", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("autor", models.CharField(max_length=200)),
                (
                    "autores",
                    models.TextField(
                        help_text="Nomes dos autores separados por vírgula"
                    ),
                ),
                ("descricao", models.TextField(blank=True, null=True)),
                ("editora", models.CharField(blank=True, max_length=100, null=True)),
                ("data_publicacao", models.DateField(blank=True, null=True)),
                ("paginas", models.PositiveIntegerField(blank=True, null=True)),
                ("capa_url", models.URLField(blank=True, max_length=500, null=True)),
                ("imagem", models.ImageField(upload_to="livros/")),
                ("idioma", models.CharField(blank=True, max_length=10, null=True)),
                (
                    "isbn",
                    models.CharField(
                        blank=True, max_length=20, null=True, verbose_name="ISBN"
                    ),
                ),
                (
                    "avaliacao_media",
                    models.FloatField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
                ("contagem_avaliacoes", models.PositiveIntegerField(default=0)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                (
                    "generos",
                    models.ManyToManyField(
                        blank=True, related_name="livros", to="nextbook_app.genero"
                    ),
                ),
            ],
            options={
                "verbose_name": "Livro",
                "verbose_name_plural": "Livros",
                "ordering": ["-criado_em"],
            },
        ),
        migrations.CreateModel(
            name="Perfil",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "livros_favoritos",
                    models.ManyToManyField(
                        blank=True, related_name="favorito_por", to="nextbook_app.livro"
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Prefere",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("data_criacao", models.DateTimeField(auto_now_add=True)),
                (
                    "genero",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="nextbook_app.genero",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GrafoLivros",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("peso", models.IntegerField(default=1)),
                (
                    "livro_destino",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recomendacoes_recebidas",
                        to="nextbook_app.livro",
                    ),
                ),
                (
                    "livro_origem",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recomendacoes_feitas",
                        to="nextbook_app.livro",
                    ),
                ),
            ],
            options={
                "unique_together": {("livro_origem", "livro_destino")},
            },
        ),
        migrations.CreateModel(
            name="Favorito",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("data_criacao", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "livro",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="nextbook_app.livro",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Favoritos",
                "unique_together": {("usuario", "livro")},
            },
        ),
    ]
