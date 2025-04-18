from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.realizar_login, name='login'),
    path('livros/', views.livros, name='livros'),
    path('livros-debug/', views.livros_debug, name='livros_debug'),
    path('favoritar_livro/<str:livro_id>/', views.favoritar_livro, name='favoritar_livro'),    path('recomendacoes/', views.recomendacoes, name='recomendacoes'),
    path('categorias/', views.categorias, name='categorias'),
    path('perfil/', views.perfil, name='perfil'),
    path('editar-perfil/', views.editar_perfil, name='editar-perfil'),
    path('logout/', views.realizar_logout, name='logout'),
    path('livro/<str:livro_id>/', views.pagina_livro, name='pagina_livro'),

]