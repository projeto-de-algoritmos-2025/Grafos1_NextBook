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
        User.objects.create_user(username=username, password=password, email=email)

        # Redirecionar para a página de login após o cadastro
        return redirect('login')

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

@login_required
def deletar_usuario(request):
    if request.method == 'POST':
        user = request.user
        logout(request)  # Desloga o usuário antes de deletar
        user.delete()  # Deleta o usuário
        return redirect('home')  # Redireciona para a página inicial

    return render(request, 'deletar_usuario.html')  # Página de confirmação

def realizar_logout(request):
    logout(request)  # Desloga o usuário
    return redirect('home')  # Redireciona para a página inicial


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

@login_required
def favoritar_livro(request, livro_id):
    livro = get_object_or_404(Livro, id=livro_id)
    usuario = request.user
    
    if request.method == 'POST':
        try:
            # Verifica se já está favoritado
            favoritado = Favorito.objects.filter(usuario=usuario, livro=livro).exists()
            
            if request.POST.get('favoritado') == 'true' and not favoritado:
                # Adiciona aos favoritos e atualiza o grafo
                Favorito.objects.create(usuario=usuario, livro=livro)
                atualizar_grafo(usuario, livro)
                return JsonResponse({'success': True, 'action': 'added'})
            elif request.POST.get('favoritado') == 'false' and favoritado:
                # Remove dos favoritos
                Favorito.objects.filter(usuario=usuario, livro=livro).delete()
                return JsonResponse({'success': True, 'action': 'removed'})
            
            return JsonResponse({'success': True, 'action': 'no_change'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)

def atualizar_grafo(usuario, livro_novo):
    # Pega os últimos 5 favoritos do usuário (excluindo o atual)
    ultimos_favoritos = Favorito.objects.filter(
        usuario=usuario
    ).exclude(livro=livro_novo).order_by('-data_favorito')[:5]
    
    for favorito in ultimos_favoritos:
        # Cria/atualiza conexões no grafo (bidirecional)
        GrafoLivros.objects.update_or_create(
            livro_origem=favorito.livro,
            livro_destino=livro_novo,
            defaults={'peso': models.F('peso') + 1}  # Incrementa o peso
        )
        
        GrafoLivros.objects.update_or_create(
            livro_origem=livro_novo,
            livro_destino=favorito.livro,
            defaults={'peso': models.F('peso') + 1}
        )
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