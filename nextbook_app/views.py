from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Livro, Favorito, GrafoLivros, Perfil
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from nextbook_app.scripts.busca_dfs import buscar_dfs
from django.contrib.auth.models import User
import requests
from django.core.paginator import Paginator
from django.conf import settings
import random
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from datetime import datetime
import json


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
            # Ensure the user has a Perfil object
            Perfil.objects.get_or_create(user=user)
            login(request, user)
            return redirect('home')
        return render(request, 'login.html', {'erro': 'Usuário ou senha inválidos.'})

    return render(request, 'login.html')

@login_required
def perfil(request):
    favoritos = Favorito.objects.filter(usuario=request.user)
    if request.method == 'POST':
        livro_id = request.POST.get('livro_id')
        if livro_id:
            Favorito.objects.filter(usuario=request.user, livro_id=livro_id).delete()
            request.user.perfil.livros_favoritos.remove(livro_id)
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

    temas = ['fiction', 'romance', 'science', 'history', 'technology', 'fantasy', 'biography']

    if random_filter:
        tema = random.choice(temas)
        start_index = random.randint(0, 100)

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

    # Salvar livros no banco de dados
    for livro in livros_data:
        volume_info = livro.get('volumeInfo', {})
        publicado_em = volume_info.get('publishedDate', None)

        # Tratar diferentes formatos de data
        if publicado_em:
            try:
                if len(publicado_em) == 4:  # Apenas o ano
                    publicado_em = datetime.strptime(publicado_em, '%Y').date()
                elif len(publicado_em) == 7:  # Ano e mês
                    publicado_em = datetime.strptime(publicado_em, '%Y-%m').date()
                else:  # Ano, mês e dia
                    publicado_em = datetime.strptime(publicado_em, '%Y-%m-%d').date()
            except ValueError:
                publicado_em = None  # Ignorar datas inválidas

        Livro.objects.get_or_create(
            id=livro['id'],
            defaults={
                'titulo': volume_info.get('title', 'Título Desconhecido'),
                'descricao': volume_info.get('description', 'Descrição não disponível'),
                'publicado_em': publicado_em,
            }
        )

        livro['capa_url'] = volume_info.get('imageLinks', {}).get('thumbnail', '/static/imgs/book-placeholder.png')

    # Ordenações
    if order == 'title':
        livros_data.sort(key=lambda x: x['volumeInfo'].get('title', '').lower())
    elif order == '-published':
        livros_data.sort(key=lambda x: x['volumeInfo'].get('publishedDate', ''), reverse=True)

    return render(request, 'livros.html', {
        'livros': livros_data,
    })

@login_required
@csrf_protect
@require_POST
def favoritar_livro(request, livro_id):
    try:
        livro = get_object_or_404(Livro, id=livro_id)
        usuario = request.user

        # Decode JSON payload
        data = json.loads(request.body.decode('utf-8'))
        favoritado = data.get('favoritado')

        if favoritado is None:
            return JsonResponse({'success': False, 'error': 'Missing "favoritado" field'}, status=400)

        with transaction.atomic():
            if favoritado:
                Favorito.objects.get_or_create(usuario=usuario, livro=livro)
                usuario.perfil.livros_favoritos.add(livro)
                atualizar_grafo(usuario, livro)
            else:
                Favorito.objects.filter(usuario=usuario, livro=livro).delete()
                usuario.perfil.livros_favoritos.remove(livro)

        return JsonResponse({'success': True, 'favoritado': favoritado})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@csrf_protect
@require_POST
def toggle_favorito(request):
    try:
        data = json.loads(request.body.decode('utf-8'))  # Decode JSON payload

        if 'livro_id' not in data or 'favoritado' not in data:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)

        livro_id = data['livro_id']
        favoritado = data['favoritado']
        livro = get_object_or_404(Livro, id=livro_id)
        usuario = request.user

        with transaction.atomic():
            if favoritado:
                Favorito.objects.get_or_create(usuario=usuario, livro=livro)
                usuario.perfil.livros_favoritos.add(livro)
            else:
                Favorito.objects.filter(usuario=usuario, livro=livro).delete()
                usuario.perfil.livros_favoritos.remove(livro)

        return JsonResponse({'success': True, 'favoritado': favoritado})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def atualizar_grafo(usuario, livro_novo):
    ultimos_favoritos = Favorito.objects.filter(
        usuario=usuario
    ).exclude(livro=livro_novo).order_by('-criado_em')[:5]
    
    for favorito in ultimos_favoritos:
        GrafoLivros.objects.update_or_create(
            livro_origem=favorito.livro,
            livro_destino=livro_novo,
            defaults={'peso': 1}
        )
        GrafoLivros.objects.update_or_create(
            livro_origem=livro_novo,
            livro_destino=favorito.livro,
            defaults={'peso': 1}
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