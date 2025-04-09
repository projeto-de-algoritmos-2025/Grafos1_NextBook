from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

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

def livros(request):
    return render(request, 'livros.html')