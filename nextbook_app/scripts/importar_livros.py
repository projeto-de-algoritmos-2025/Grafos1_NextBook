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

def normalizar_genero(nome_genero):
    """Normaliza o nome do gênero para consistência"""
    return nome_genero.strip().lower().capitalize()

def importar_livros():
    for genero_busca in GENRES:
        print(f"🔍 Buscando livros de gênero: {genero_busca}")
        params = {
            'q': genero_busca,
            'maxResults': MAX_RESULTS,
            'langRestrict': 'pt',
            'printType': 'books',
        }

        try:
            response = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao buscar livros de {genero_busca}: {str(e)}")
            continue

        livros = response.json().get('items', [])
        print(f"📘 {len(livros)} livros encontrados para {genero_busca}.")

        for item in livros:
            try:
                volume_info = item.get('volumeInfo', {})
                titulo = volume_info.get('title', 'Sem título')
                if not titulo or titulo == 'Sem título':
                    continue

                slug = slugify(titulo)
                sinopse = volume_info.get('description', 'Sem sinopse.')
                capa = volume_info.get('imageLinks', {}).get('thumbnail', '')
                avaliacao = volume_info.get('averageRating', 0)
                autores = volume_info.get('authors', ['Desconhecido'])
                autor = autores[0] if autores else 'Desconhecido'
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
                except ValueError:
                    dt_publicacao = datetime.strptime("2000-01-01", "%Y-%m-%d").date()

                # Criar ou atualizar LivroTitulo
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

                # Criar ou atualizar Livro
                livro_obj, _ = Livro.objects.update_or_create(
                    titulo=livro_titulo,
                    defaults={
                        'autor': autor,
                        'editora': editora,
                        'num_paginas': num_paginas,
                    }
                )

                # Processar gêneros
                categorias = volume_info.get('categories', [genero_busca])
                generos_processados = set()
                
                for categoria in categorias:
                    if not categoria:
                        continue
                    # Dividir categorias que podem vir como "Ficção/Romance"
                    for sub_categoria in categoria.split('/'):
                        nome_genero = normalizar_genero(sub_categoria)
                        if nome_genero in GENRES and nome_genero not in generos_processados:
                            generos_processados.add(nome_genero)
                            genero, _ = GeneroLivro.objects.get_or_create(nome_genero=nome_genero)
                            PossuiGeneroLivro.objects.get_or_create(titulo=livro_titulo, genero=genero)

                print(f"✅ Importado: {titulo}")
            except Exception as e:
                print(f"⚠️ Erro ao processar livro: {str(e)}")
                continue
