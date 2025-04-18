import json
from collections import defaultdict

# Função para carregar o grafo a partir de um arquivo JSON
def carregar_grafo():
    try:
        with open('nextbook_app/static/grafo.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise Exception("Arquivo grafo.json não encontrado. Execute criar_grafo.py primeiro.")
    except json.JSONDecodeError:
        raise Exception("Erro ao decodificar o arquivo grafo.json. Verifique o formato do arquivo.")

# Função para realizar a busca em profundidade (DFS)
def dfs(grafo, inicio, max_profundidade=3):
    visitados = set()
    pilha = [(inicio, 0)]
    recomendacoes = defaultdict(int)
    
    while pilha:
        livro_id, profundidade = pilha.pop()
        
        if profundidade >= max_profundidade:
            continue
            
        if livro_id not in visitados:
            visitados.add(livro_id)
            
            # Adiciona livros relacionados à pilha
            for relacionamento in grafo["relacionamentos"]["livro-livro"]:
                if livro_id in relacionamento:
                    outro_livro = relacionamento[0] if relacionamento[1] == livro_id else relacionamento[1]
                    if outro_livro not in visitados:
                        pilha.append((outro_livro, profundidade + 1))
                        recomendacoes[outro_livro] += (max_profundidade - profundidade)
    
    # Ordena recomendações por peso (e depois por avaliação)
    livros_ordenados = sorted(
        recomendacoes.keys(),
        key=lambda x: (-recomendacoes[x], -grafo["livros"][x]["avaliacao"])
    )
    
    return [grafo["livros"][livro_id] for livro_id in livros_ordenados if livro_id != inicio]

# Função para buscar as recomendações de livros com base no livro inicial
def buscar_recomendacoes(slug_livro, max_recomendacoes=5):
    grafo = carregar_grafo()
    
    # Encontra o livro pelo slug
    livro_inicio = None
    for livro_id, livro_data in grafo["livros"].items():
        if livro_data["slug"] == slug_livro:
            livro_inicio = livro_id
            break
    
    if not livro_inicio:
        print(f"Erro: Livro com slug '{slug_livro}' não encontrado.")
        return []
    
    recomendacoes = dfs(grafo, livro_inicio)[:max_recomendacoes]
    
    # Adiciona critério de categoria na recomendação
    livros_recomendados = []
    categoria_inicial = grafo["livros"][livro_inicio].get("categoria", None)
    
    for livro in recomendacoes:
        if livro.get("categoria") == categoria_inicial:
            livros_recomendados.append(livro)
    
    print(f"Recomendações para '{slug_livro}': {[livro['titulo'] for livro in livros_recomendados]}")
    return livros_recomendados

# Função para implementar a busca DFS com base nos livros favoritos do usuário
def buscar_dfs(usuario):
    grafo = carregar_grafo()
    livros_favoritos = Favorito.objects.filter(usuario=usuario).values_list('livro_id', flat=True)
    recomendacoes_totais = []

    for livro_id in livros_favoritos:
        recomendacoes = dfs(grafo, str(livro_id))
        recomendacoes_totais.extend(recomendacoes)

    recomendacoes_unicas = {livro['id']: livro for livro in recomendacoes_totais}.values()
    return sorted(recomendacoes_unicas, key=lambda x: -x['avaliacao'])
