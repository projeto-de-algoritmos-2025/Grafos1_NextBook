from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.realizar_login, name='login'),
    path('livros/', views.livros, name='livros'),
    path('livro/<slug:slug>/', views.detalhe_livro, name='detalhe_livro'),
    path('livro/favoritar/<int:titulo_id>/', views.toggle_favorito_livro, name='toggle_favorito_livro'),
]
