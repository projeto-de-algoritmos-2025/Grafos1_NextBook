from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.conf import settings
from django.core.cache import cache
from django.views.decorators.cache import cache_page
import requests
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
import random
from datetime import datetime
from django.views.decorators.http import require_POST


def home(request):
    return render(request, 'index.html')

def cadastro(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            user.save()
            return redirect('login')
        except Exception as e:
            return render(request, 'cadastro.html', {'erro': str(e)})

    return render(request, 'cadastro.html')

def realizar_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        return render(request, 'login.html', {'erro': 'Usuário ou senha inválidos.'})

    return render(request, 'login.html')

@login_required
def perfil(request):
    usuario = request.user
    favoritos = Favorito.objects.filter(usuario=usuario) if hasattr(usuario, 'favorito_set') else None

    context = {
        'username': usuario.username,
        'email': usuario.email,
        'nome_completo': f"{usuario.first_name} {usuario.last_name}",
        'favoritos': favoritos,
    }

    return render(request, 'perfil.html', context)

@login_required
def editar_perfil(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.username = request.POST.get('username', '')
        user.email = request.POST.get('email', '')

        password = request.POST.get('password')
        if password:
            user.set_password(password)
            login(request, user)  

        user.save()
        return redirect('perfil')

    return render(request, 'editar-perfil.html', {'user': user})

def realizar_logout(request):
    logout(request)
    return redirect('login')

def livros(request):
    """View para listagem de livros com opções de ordenação e fallback para mock"""
    from datetime import datetime  # Garante que o datetime está importado

    # Função auxiliar para converter a data corretamente
    def parse_date(date_str):
        """Tenta converter data em formatos diferentes"""
        formats = ['%Y-%m-%d', '%Y-%m', '%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except (ValueError, TypeError):
                continue
        return datetime.min

    DEFAULT_COUNT = 12
    MAX_RESULTS = 40
    order_by = request.GET.get('order')
    
    try:
        # Busca livros na API
        params = {
            'q': 'lang:pt',
            'maxResults': MAX_RESULTS,
            'key': settings.GOOGLE_BOOKS_API_KEY
        }
        response = requests.get('https://www.googleapis.com/books/v1/volumes', params=params)
        response.raise_for_status()
        
        all_books = response.json().get('items', [])
        
        # Seleciona livros (aleatórios sem filtro, ou os primeiros com filtro)
        if not order_by:
            livros = random.sample(all_books, min(DEFAULT_COUNT, len(all_books))) if all_books else []
        else:
            livros = all_books[:DEFAULT_COUNT]
        
        # filtros/ordenação
        if order_by == 'title':
            livros.sort(key=lambda x: x['volumeInfo'].get('title', '').lower())
        elif order_by == '-title':
            livros.sort(key=lambda x: x['volumeInfo'].get('title', '').lower(), reverse=True)
        elif order_by == 'average_rating':
            livros.sort(key=lambda x: x['volumeInfo'].get('averageRating', 0))
        elif order_by == '-average_rating':
            livros.sort(key=lambda x: x['volumeInfo'].get('averageRating', 0), reverse=True)
        elif order_by == 'published_date':
            livros.sort(key=lambda x: parse_date(x['volumeInfo'].get('publishedDate', '')), reverse=False)
        elif order_by == '-published_date':
            livros.sort(key=lambda x: parse_date(x['volumeInfo'].get('publishedDate', '')), reverse=True)

        # Paginação
        paginator = Paginator(livros, DEFAULT_COUNT)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'livros.html', {
            'livros': page_obj,
            'is_paginated': paginator.num_pages > 1,
            'page_obj': page_obj,
            'current_order': order_by  # Para manter o filtro ativo na template
        })
        
    except Exception as e:
        print(f"Erro ao buscar livros: {str(e)}")
        livros_mock = [
            {
                'id': f'mock{i}',
                'volumeInfo': {
                    'title': f'Livro Exemplo {i+1}',
                    'authors': ['Autor Brasileiro'],
                    'publishedDate': str(2020 + i),
                    'imageLinks': {'thumbnail': f'https://via.placeholder.com/128x193.png?text=Exemplo+{i+1}'},
                    'language': 'pt',
                    'averageRating': random.randint(1, 5)
                }
            } for i in range(DEFAULT_COUNT)
        ]
        return render(request, 'livros.html', {
            'livros': livros_mock,
            'current_order': None
        })

def categorias(request):
    return render(request, 'categorias.html') 

def recomendacoes(request):
    return render(request, 'recomendacoes.html', {})

@cache_page(60 * 15)
def pagina_livro(request, livro_id):
    return pagina_livros(request, livro_id)


@cache_page(60 * 15)  # Cache de 15 minutos
def pagina_livros(request, livro_id):
    """
    View para exibir detalhes de um livro específico
    """
    # Verifica se a API key está configurada
    if not getattr(settings, 'GOOGLE_BOOKS_API_KEY', None):
        raise ImproperlyConfigured("GOOGLE_BOOKS_API_KEY não está configurada no settings.py")
    
    try:
        # Busca na API do Google Books
        response = requests.get(
            f'https://www.googleapis.com/books/v1/volumes/{livro_id}',
            params={'key': settings.GOOGLE_BOOKS_API_KEY}
        )
        response.raise_for_status()
        livro_data = response.json()
    except requests.RequestException as e:
        raise Http404("Livro não encontrado")

    volume_info = livro_data.get('volumeInfo', {})
    sale_info = livro_data.get('saleInfo', {})

    esta_favorito = False
    if request.user.is_authenticated:
        esta_favorito = request.user.favorito_set.filter(livro_google_id=livro_id).exists()

    context = {
        'livro_id': livro_id,
        'volumeInfo': volume_info, 
        'saleInfo': sale_info,
        'esta_favorito': esta_favorito,
        'autores': ', '.join(volume_info.get('authors', ['Autor desconhecido'])),
        'categorias': ', '.join(volume_info.get('categories', ['Sem categoria'])),
        'isbn': next(
            (id['identifier'] for id in volume_info.get('industryIdentifiers', []) 
            if id['type'] == 'ISBN_13'), ''),
    }

    return render(request, 'pagina_livro.html', context)

@require_POST
@login_required
def adicionar_favorito(request, livro_id):
    try:
        # Obter dados adicionais do livro do corpo da requisição
        data = json.loads(request.body)
        titulo = data.get('titulo', '')
        autor = data.get('autor', '')
        capa_url = data.get('capa_url', '')
        
        # Verifica se já é favorito
        favorito, created = Favorito.objects.get_or_create(
            usuario=request.user,
            livro_google_id=livro_id,
            defaults={
                'titulo': titulo,
                'autor': autor,
                'capa_url': capa_url
            }
        )
        
        if not created:
            favorito.delete()
            action = 'removed'
        else:
            action = 'added'

        return JsonResponse({
            'success': True,
            'action': action,
            'contagem': request.user.favorito_set.count()
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def buscar_similares(request, livro_id):
    try:
        # Primeiro busca as categorias do livro atual
        livro_response = requests.get(
            f'https://www.googleapis.com/books/v1/volumes/{livro_id}',
            params={'key': settings.GOOGLE_BOOKS_API_KEY}
        )
        livro_response.raise_for_status()
        livro_data = livro_response.json()
        
        categorias = livro_data.get('volumeInfo', {}).get('categories', ['general'])
        categoria_principal = categorias[0]

        # Busca livros similares
        response = requests.get(
            'https://www.googleapis.com/books/v1/volumes',
            params={
                'q': f'subject:{categoria_principal}',
                'maxResults': 4,
                'key': settings.GOOGLE_BOOKS_API_KEY
            }
        )
        response.raise_for_status()
        data = response.json()

        # Filtra para não incluir o livro atual
        similares = [
            livro for livro in data.get('items', []) 
            if livro['id'] != livro_id
        ][:3]  # Limita a 3 resultados

        # Prepara os dados para o template
        livros_similares = []
        for livro in similares:
            volume_info = livro.get('volumeInfo', {})
            livros_similares.append({
                'id': livro['id'],
                'titulo': volume_info.get('title', 'Título desconhecido'),
                'autor': volume_info.get('authors', ['Autor desconhecido'])[0],
                'capa': volume_info.get('imageLinks', {}).get('thumbnail', '')
            })

        return JsonResponse({
            'status': 'success',
            'livros': livros_similares
        })

    except requests.RequestException as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
 # views.py
def livros_debug(request):
    livros = [
        {
            'id': 'bM_MhU5SUWsC',
            'volumeInfo': {
                'title': 'A criança surda',
                'authors': ['Marcia Goldfeld'],
                'publishedDate': '2002',
                'imageLinks': {
                    'thumbnail': 'http://books.google.com/books/content?id=bM_MhU5SUWsC&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
                },
                'language': 'pt',
                'averageRating': 4
            }
        },
        
    ]
    
    return render(request, 'livros.html', {'livros': livros})