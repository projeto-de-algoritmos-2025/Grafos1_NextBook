from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import User
from .models import Livro, LivroTitulo, GeneroLivro, PossuiGeneroLivro, FavoritoLivro
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Q
from django.contrib import messages

def home(request):
    return render(request, 'index.html')

def livros(request):
    livros = Livro.objects.select_related('titulo').order_by('-id_livro')[:12]
    return render(request, 'livros.html', {'livros': livros})

def detalhe_livro(request, slug):
    titulo = get_object_or_404(LivroTitulo, slug=slug)
    livro = get_object_or_404(Livro, titulo=titulo)
    generos = GeneroLivro.objects.filter(possuilivrogenero__titulo=titulo)

    is_favorito = titulo.favoritolivro_set.filter(usuario=request.user).exists() if request.user.is_authenticated else False

    context = {
        'livro': livro,
        'generos': generos,
        'is_favorito': is_favorito,
    }
    return render(request, 'detalhe_livro.html', context)

def filtro_livros(request):
    genero = request.GET.get('genero')
    nota = request.GET.get('nota')

    livros = Livro.objects.select_related('titulo')

    if genero:
        livros = livros.filter(titulo__possuigenerolivro__genero__nome_genero__iexact=genero)
    if nota:
        livros = livros.filter(titulo__avaliacao__gte=nota)

    generos = GeneroLivro.objects.all()
    return render(request, 'filtro_livros.html', {
        'livros': livros,
        'generos': generos
    })

@login_required
def toggle_favorito_livro(request, titulo_id):
    titulo = get_object_or_404(LivroTitulo, id=titulo_id)
    favorito, created = FavoritoLivro.objects.get_or_create(usuario=request.user, titulo=titulo)

    if not created:
        favorito.delete()
        messages.success(request, f"'{titulo.titulo}' foi removido dos seus favoritos.")
    else:
        messages.success(request, f"'{titulo.titulo}' foi adicionado aos seus favoritos.")

    return redirect('detalhe_livro', slug=titulo.slug)


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
    favoritos = Favorita.objects.filter(usuario=request.user)
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


def fazer_logout(request):
    logout(request)
    return redirect('home')

