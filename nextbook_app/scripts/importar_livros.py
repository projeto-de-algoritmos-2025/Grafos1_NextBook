import requests
from datetime import datetime
from django.utils.text import slugify
from nextbook_app.models import Livro, LivroTitulo, GeneroLivro, PossuiGeneroLivro

GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
MAX_RESULTS = 40

GENRES = [
    "ficção", "romance", "fantasia", "terror", "aventura", "mistério",
    "drama", "biografia", "poesia", "humor", "distopia", "tecnologia"
]

def importar_livros():
    for genero_busca in GENRES:
        print(f"🔍 Buscando livros de gênero: {genero_busca}")
        params = {
            'q': genero_busca,
            'maxResults': MAX_RESULTS,
            'langRestrict': 'pt',
            'printType': 'books',
        }

        response = requests.get(GOOGLE_BOOKS_API, params=params)
        if response.status_code != 200:
            print(f"❌ Erro ao buscar livros de {genero_busca}: {response.status_code}")
            continue

        livros = response.json().get('items', [])
        print(f"📘 {len(livros)} livros encontrados para {genero_busca}.")

        for item in livros:
            volume_info = item.get('volumeInfo', {})

            titulo = volume_info.get('title', 'Sem título')
            slug = slugify(titulo)
            sinopse = volume_info.get('description', 'Sem sinopse.')
            capa = volume_info.get('imageLinks', {}).get('thumbnail', '')
            avaliacao = volume_info.get('averageRating', 0)
            autor = volume_info.get('authors', ['Desconhecido'])[0]
            editora = volume_info.get('publisher', 'Desconhecida')
            num_paginas = volume_info.get('pageCount', 0)

            data_raw = volume_info.get('publishedDate', '2000-01-01')
            try:
                if len(data_raw) == 4:
                    dt_publicacao = datetime.strptime(data_raw, "%Y").date()
                elif len(data_raw) == 7:
                    dt_publicacao = datetime.strptime(data_raw, "%Y-%m").date()
                else:
                    dt_publicacao = datetime.strptime(data_raw, "%Y-%m-%d").date()
            except Exception:
                dt_publicacao = datetime.strptime("2000-01-01", "%Y-%m-%d").date()

            livro_titulo, _ = LivroTitulo.objects.update_or_create(
                slug=slug,
                defaults={
                    'titulo': titulo,
                    'dt_publicacao': dt_publicacao,
                    'sinopse': sinopse,
                    'capaPath': capa,
                    'avaliacao': avaliacao,
                }
            )

            livro_obj, _ = Livro.objects.update_or_create(
                titulo=livro_titulo,
                defaults={
                    'autor': autor,
                    'editora': editora,
                    'num_paginas': num_paginas,
                }
            )
            categorias = volume_info.get('categories')
            if not categorias:
                categorias = [genero_busca.title()]
           # Normaliza os nomes dos gêneros
            for categoria in categorias:
                nome_genero = categoria.strip().lower().capitalize()
                genero, _ = GeneroLivro.objects.get_or_create(nome_genero=nome_genero)
                PossuiGeneroLivro.objects.get_or_create(titulo=livro_titulo, genero=genero)

            # Pega os gêneros da API e se não encontrarnada usa o genero_busca da lista GENRES
            # Depois cria um gênero na tabela caso ainda não exista e cria uma associação ente livros desse gênero em PossuiGeneroLivro
            for categoria in volume_info.get('categories', [genero_busca.title()]):
                genero, _ = GeneroLivro.objects.get_or_create(nome_genero=categoria)
                PossuiGeneroLivro.objects.get_or_create(titulo=livro_titulo, genero=genero)

            print(f"✅ Importado: {titulo}")

