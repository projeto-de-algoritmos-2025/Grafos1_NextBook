import json
from nextbook_app.models import LivroTitulo, GeneroLivro, PossuiGeneroLivro

def criar_grafo():
    # Inicializando o grafo corretamente
    grafo = {
        "generos": {},
        "livros": {},
        "relacionamentos": {
            "livro-genero": {},
            "livro-livro": []
        }
    }

    # Populando o grafo com dados dos gêneros
    for genero in GeneroLivro.objects.all():
        print(f"Adicionando gênero: {genero.nome_genero}")  # Debug
        grafo["generos"][str(genero.id)] = genero.nome_genero
    
    # Populando o grafo com dados dos livros
    for livro_titulo in LivroTitulo.objects.all():
        livro_id = str(livro_titulo.id)
        print(f"Adicionando livro: {livro_titulo.titulo}")  # Debug
        grafo["livros"][livro_id] = {
            "id": livro_titulo.id,
            "titulo": livro_titulo.titulo,
            "avaliacao": livro_titulo.avaliacao,
            "slug": livro_titulo.slug
        }

        # Relacionamento livro-genero
        generos_livro = PossuiGeneroLivro.objects.filter(titulo=livro_titulo)
        if generos_livro.exists():
            grafo["relacionamentos"]["livro-genero"][livro_id] = [
                str(g.genero.id) for g in generos_livro
            ]

    # Criando relacionamentos livro-livro (livros que compartilham gêneros)
    relacionamentos = set()  # Para evitar duplicatas
    for livro1_id in grafo["relacionamentos"]["livro-genero"]:
        generos_livro1 = set(grafo["relacionamentos"]["livro-genero"][livro1_id])
        for livro2_id in grafo["relacionamentos"]["livro-genero"]:
            if livro1_id == livro2_id:
                continue
            generos_livro2 = set(grafo["relacionamentos"]["livro-genero"][livro2_id])
            if generos_livro1 & generos_livro2:  # Se há intersecção de gêneros
                relacao = tuple(sorted((livro1_id, livro2_id)))
                relacionamentos.add(relacao)

    grafo["relacionamentos"]["livro-livro"] = [list(r) for r in relacionamentos]

    # Salvando o grafo
    with open('nextbook_app/static/grafo.json', 'w', encoding='utf-8') as arquivo:
        json.dump(grafo, arquivo, indent=4, ensure_ascii=False)

    print("Grafo salvo com sucesso!")
    return grafo
