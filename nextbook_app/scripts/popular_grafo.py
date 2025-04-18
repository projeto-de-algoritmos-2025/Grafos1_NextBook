import json
from nextbook_app.models import Livro, GrafoLivros

def popular_grafo():
    livros = Livro.objects.all()
    
    # Cria conexões aleatórias para demonstração
    for livro in livros:
        for _ in range(3):  # 3 recomendações por livro
            livro_destino = Livro.objects.order_by('?').first()
            if livro != livro_destino:
                GrafoLivros.objects.create(
                    livro_origem=livro,
                    livro_destino=livro_destino,
                    peso=1
                )

if __name__ == "__main__":
    popular_grafo()