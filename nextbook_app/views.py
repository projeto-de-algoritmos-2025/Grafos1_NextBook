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
from django.views.decorators.http import require_POST
from .models import Livro, Perfil, Favorito
from django.views.decorators.csrf import csrf_exempt
import json


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

    context = {
        'username': usuario.username,
        'email': usuario.email,
        'nome_completo': f"{usuario.first_name} {usuario.last_name}",
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


def pagina_livro(request, livro_id):
    print(f"ID do livro recebido: {livro_id}")  # Debug
    
    try:
        api_url = f"https://www.googleapis.com/books/v1/volumes/{livro_id}"
        print(f"URL da API: {api_url}")  # Debug
        
        response = requests.get(api_url)
        print(f"Status code: {response.status_code}")  # Debug
        
        response.raise_for_status()
        
        livro_api = response.json()
        google_id = livro_api.get('id')
        titulo = livro_api.get('volumeInfo', {}).get('title', 'Título não encontrado')
        print(f"Dados recebidos: {titulo}")  # Debug
        
        try:
            livro = Livro.objects.get(google_id=google_id)
        except Livro.DoesNotExist:
            livro = None
    
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a API: {e}")
        livro = None
    
    context = {
        'livro': livro,
    }
    
    return render(request, 'pagina_livro.html', context)


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



@require_POST
@login_required
def favoritar_livro(request, livro_id):
    try:
        data = json.loads(request.body)
        if request.POST.get('favoritar') == 'true':
            Favorito.objects.get_or_create(
                usuario=request.user,
                livro_id=livro_id
            )
        else:
            Favorito.objects.filter(
                usuario=request.user,
                livro_id=livro_id
            ).delete()
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@login_required
def configurar_preferencias(request):
    if request.method == 'POST':
        livros_ids = request.POST.getlist('livros')
        for livro_id in livros_ids:
            # Busca os dados do livro na API do Google Books
            api_url = f"https://www.googleapis.com/books/v1/volumes/{livro_id}"
            try:
                response = requests.get(api_url)
                response.raise_for_status()
                livro_api = response.json()
                titulo = livro_api.get('volumeInfo', {}).get('title', 'Título não encontrado')
                autor = ', '.join(livro_api.get('volumeInfo', {}).get('authors', ['Autor desconhecido']))
                capa_url = livro_api.get('volumeInfo', {}).get('imageLinks', {}).get('thumbnail', '')

                # Cria ou busca o favorito no banco de dados
                Favorito.objects.get_or_create(
                    usuario=request.user,
                    livro_id=livro_id,
                    defaults={'data_criacao': None}  # Define valores padrão, se necessário
                )
            except Exception as e:
                print(f"Erro ao buscar ou criar favorito: {e}")
        return redirect('perfil')  # Redireciona para o perfil após salvar

    # Busca livros já favoritados pelo usuário
    favoritos = Favorito.objects.filter(usuario=request.user).values_list('livro_id', flat=True)

    # Busca livros da API do Google Books
    try:
        params = {
            'q': 'lang:pt',
            'maxResults': 20,  # Limite de 20 livros
            'key': settings.GOOGLE_BOOKS_API_KEY
        }
        response = requests.get('https://www.googleapis.com/books/v1/volumes', params=params)
        response.raise_for_status()
        livros_api = response.json().get('items', [])
    except Exception as e:
        print(f"Erro ao buscar livros da API: {e}")
        livros_api = []

    # Exclui os livros já favoritados
    livros_disponiveis = [livro for livro in livros_api if livro['id'] not in favoritos]

    return render(request, 'configurar_preferencias.html', {
        'livros': livros_disponiveis,
    })

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