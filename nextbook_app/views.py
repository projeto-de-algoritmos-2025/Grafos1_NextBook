from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Livro, Favorito, GrafoLivros
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from nextbook_app.scripts.busca_dfs import buscar_dfs
from django.contrib.auth.models import User
import requests
from django.core.paginator import Paginator
from django.conf import settings
import random
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404


# Função para renderizar a home page
def home(request):
    return render(request, 'index.html')

# Função para cadastro de novos usuários
def cadastro(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        # Verificar se o nome de usuário já existe
        if User.objects.filter(username=username).exists():
            return render(request, 'cadastro.html', {'error': 'Nome de usuário já existe.'})

        # Criar um novo usuário
        user = User.objects.create_user(username=username, password=password, email=email)

        # Redirecionar ou renderizar uma página de sucesso
        return render(request, 'cadastro.html', {'success': 'Usuário criado com sucesso!'})

    return render(request, 'login.html')


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
    favoritos = Favorito.objects.filter(usuario=request.user)
    context = {
        'username': request.user.username,
        'email': request.user.email,
        'nome_completo': request.user.get_full_name(),
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
    return redirect('home')


def livros_debug(request):
    livros = Livro.objects.all()

    livros_data = [
        {'id': livro.id, 'titulo': livro.titulo, 'autor': livro.autor} for livro in livros
    ]
    
    return JsonResponse({'livros': livros_data})


def livros(request):
    order = request.GET.get('order')
    random_filter = request.GET.get('random')

    livros_data = []

    # Lista de temas aleatórios (pode adicionar mais)
    temas = ['fiction', 'romance', 'science', 'history', 'technology', 'fantasy', 'biography']

    if random_filter:
        tema = random.choice(temas)
        start_index = random.randint(0, 100)  # Pega a partir de um ponto aleatório

        try:
            response = requests.get(
                f'https://www.googleapis.com/books/v1/volumes?q=subject:{tema}'
                f'&key={settings.GOOGLE_BOOKS_API_KEY}&startIndex={start_index}&maxResults=40'
            )
            response.raise_for_status()
            livros_data = response.json().get('items', [])
        except requests.exceptions.RequestException as e:
            print(f"Erro na API (aleatório): {e}")
            livros_data = []

    else:
        for start_index in range(0, 40, 10):
            try:
                response = requests.get(
                    f'https://www.googleapis.com/books/v1/volumes?q=subject:fiction'
                    f'&key={settings.GOOGLE_BOOKS_API_KEY}&startIndex={start_index}&maxResults=10'
                )
                response.raise_for_status()
                blocos = response.json().get('items', [])
                if blocos:
                    livros_data.extend(blocos)
            except requests.exceptions.RequestException as e:
                print(f"Erro na API: {e}")

    # Ordenações
    if order == 'title':
        livros_data.sort(key=lambda x: x['volumeInfo'].get('title', '').lower())
    elif order == '-published':
        livros_data.sort(key=lambda x: x['volumeInfo'].get('publishedDate', ''), reverse=True)

    return render(request, 'livros.html', {
        'livros': livros_data,
    })

@csrf_exempt  
@require_POST
@login_required
def favoritar_livro(request, livro_id):
    try:
        # Verifica se o livro existe
        livro = Livro.objects.get(id=livro_id)
        usuario = request.user

        # Verifica se a ação é para favoritar ou desfavoritar
        favoritar = request.POST.get('favoritar') == 'true'

        # Obtendo ou criando o favorito
        favorito, created = Favorito.objects.get_or_create(usuario=usuario, livro=livro)

        if favoritar:
            if created:
                favorito.save()  # Caso o favorito tenha sido criado
            response_data = {
                'success': True,
                'favoritado': True,
                'message': 'Livro favoritado com sucesso.'
            }
        else:
            favorito.delete()  # Remove o favorito
            response_data = {
                'success': True,
                'favoritado': False,
                'message': 'Livro removido dos favoritos.'
            }

        return JsonResponse(response_data)

    except Livro.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Livro não encontrado.'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao processar a requisição: {str(e)}'})

# Função para recomendação de livros baseada nos gêneros favoritos do usuário
def recomendacoes(request, livro_id):
    # Pega as 5 recomendações mais fortes para o livro
    recomendacoes = GrafoLivros.objects.filter(
        livro_origem_id=livro_id
    ).order_by('-peso')[:5]
    
    return render(request, 'recomendacoes.html', {
        'recomendacoes': recomendacoes,
        'livro_origem': Livro.objects.get(id=livro_id)
    })

from django.shortcuts import render
from .models import Livro, GrafoLivros, Favorito

def minhas_recomendacoes(request):
    if not request.user.is_authenticated:
        # Redirecionar para login ou mostrar mensagem
        return render(request, 'recomendacoes.html', {
            'error': 'Você precisa estar logado para ver recomendações'
        })

    # Pega os livros favoritados pelo usuário
    favoritos_ids = Favorito.objects.filter(usuario=request.user).values_list('livro_id', flat=True)
    
    # Pega recomendações baseadas nos favoritos
    recomendacoes = GrafoLivros.objects.filter(
        livro_origem_id__in=favoritos_ids
    ).select_related('livro_destino').order_by('-peso')[:10]  # Top 10 recomendações

    return render(request, 'recomendacoes.html', {
        'recomendacoes': recomendacoes,
        'favoritos_ids': list(favoritos_ids),
        'titulo_pagina': 'Suas Recomendações Pessoais'
    })

def recomendacoes_livro(request, livro_id):
    livro = Livro.objects.get(id=livro_id)
    recomendacoes = GrafoLivros.objects.filter(
        livro_origem=livro
    ).select_related('livro_destino').order_by('-peso')[:5]  # Top 5 recomendações

    return render(request, 'recomendacoes.html', {
        'recomendacoes': recomendacoes,
        'livro_origem': livro,
        'titulo_pagina': f'Recomendações baseadas em "{livro.titulo}"'
    })

def livro_detail(request, livro_id):
    livro = get_object_or_404(Livro, id=livro_id)
    
    # Busca recomendações baseadas no grafo
    recomendacoes = GrafoLivros.objects.filter(
        livro_origem=livro
    ).select_related('livro_destino').order_by('-peso')[:5]  # Top 5 recomendações
    
    return render(request, 'livro_detail.html', {
        'livro': livro,
        'recomendacoes': recomendacoes
    })