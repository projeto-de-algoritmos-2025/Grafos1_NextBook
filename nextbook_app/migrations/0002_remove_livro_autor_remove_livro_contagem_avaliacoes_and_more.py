# Generated by Django 5.1.4 on 2025-04-18 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nextbook_app", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="livro",
            name="autor",
        ),
        migrations.RemoveField(
            model_name="livro",
            name="contagem_avaliacoes",
        ),
        migrations.RemoveField(
            model_name="livro",
            name="generos",
        ),
        migrations.RemoveField(
            model_name="livro",
            name="google_id",
        ),
        migrations.RemoveField(
            model_name="livro",
            name="imagem",
        ),
        migrations.RemoveField(
            model_name="livro",
            name="paginas",
        ),
        migrations.AddField(
            model_name="livro",
            name="capa",
            field=models.ImageField(blank=True, null=True, upload_to="livros/"),
        ),
        migrations.AlterField(
            model_name="livro",
            name="id",
            field=models.CharField(max_length=255, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="livro",
            name="isbn",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name="livro",
            name="slug",
            field=models.SlugField(blank=True, max_length=200, unique=True),
        ),
    ]
