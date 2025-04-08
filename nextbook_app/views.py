from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

def home(request):
    return render(request, 'index.html')

def cadastro(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.save()
            return redirect('login')
        except Exception as e:
            return render(request, 'cadastro.html', {'erro': str(e)})
    return render(request, 'cadastro.html')

def realizar_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        return render(request, 'login.html', {'erro': 'Usuário ou senha inválidos.'})
    return render(request, 'login.html')
